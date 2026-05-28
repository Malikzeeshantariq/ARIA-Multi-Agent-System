import sys
import os

# Windows cp1252 fix: must be set before Python starts for full effect.
# The real guard is PYTHONUTF8=1 in the launch script (start.ps1/start.bat).
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import queue
import threading

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError
# ✅ pydantic 2.x — BaseModel import unchanged
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from agents.orchestrator import run_research_pipeline
from agents.export_agent import export_to_pdf, export_to_word
from agents.memory_agent import (
    get_stats,
    get_all_posts,
    get_favorite_topics,
    add_document,
    list_documents,
    search_documents,
)
from sqlalchemy.orm import Session
from api.auth import router as auth_router, get_current_user
from database.connection import create_tables, SessionLocal, get_db
from database.models import User, BlogPost

load_dotenv()

app = FastAPI(
    title="Multi-Agent AI Research System",
    description="5 autonomous AI agents that research, write, and generate blog content",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth router ────────────────────────────────────────────────
app.include_router(auth_router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(request: Request, exc: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content={"detail": "Database unavailable. Check your DATABASE_URL in .env."},
    )


@app.on_event("startup")
def on_startup():
    """Create DB tables on first run."""
    try:
        create_tables()
        print("[DB] Tables created / verified OK")
    except Exception as e:
        print(f"[DB] WARNING: Could not connect to database: {e}")
        print("[DB] Set DATABASE_URL in .env to enable auth")


# ── Request Models (pydantic 2.x) ──────────────────────────────

class ResearchRequest(BaseModel):
    topic: str

    # ✅ pydantic 2.x — @validator replaced with @field_validator
    @field_validator("topic")
    @classmethod
    def topic_must_not_be_empty(cls, v: str) -> str:
        if not v or len(v.strip()) < 3:
            raise ValueError("Topic must be at least 3 characters")
        return v.strip()


class ExportRequest(BaseModel):
    topic: str
    content: str
    image_url: str = ""
    format: str = "pdf"   # "pdf" or "word"


class DocumentRequest(BaseModel):
    text: str
    source: str = "uploaded_document"


class HistoryPostSummary(BaseModel):
    id: str
    topic: str
    word_count: int
    image_count: int
    created_at: str
    content_preview: str


class HistoryPostFull(BaseModel):
    id: str
    topic: str
    content: str
    images: list
    word_count: int
    created_at: str


# ── Routes ─────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "Multi-Agent AI Research System",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "research": "POST /research",
            "export": "POST /export",
            "health": "GET /health",
            "docs": "GET /docs",
        },
    }


@app.get("/health")
async def health():
    return {"status": "healthy", "version": "2.0.0"}


# ── Memory / ChromaDB Endpoints ────────────────────────────────

@app.get("/memory/stats")
async def memory_stats():
    """Return ChromaDB collection counts."""
    return get_stats()


@app.get("/memory/posts")
async def memory_posts(limit: int = 20):
    """Return all saved blog posts (most recent first)."""
    return {"posts": get_all_posts(limit=limit)}


@app.get("/memory/topics")
async def memory_topics(n: int = 10):
    """Return top-n most searched topics."""
    return {"topics": get_favorite_topics(n=n)}


@app.get("/memory/documents")
async def memory_documents():
    """List all documents stored in the document base."""
    return {"documents": list_documents()}


@app.post("/memory/documents")
async def upload_document(request: DocumentRequest):
    """
    Add a document to the ChromaDB document base.
    The text will be chunked and made searchable for future research.
    """
    if not request.text or len(request.text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Text too short (min 50 characters)")

    chunks = add_document(request.text, source=request.source)
    return {
        "message": f"Document '{request.source}' added successfully",
        "chunks_created": chunks,
        "source": request.source,
    }


@app.get("/memory/search")
async def memory_search(q: str, n: int = 5):
    """Search the document base for a query."""
    result = search_documents(q, n_results=n)
    return {"query": q, "result": result or "No matching documents found"}


@app.get("/history")
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50,
):
    """Return the authenticated user's research history, newest first."""
    posts = (
        db.query(BlogPost)
        .filter(BlogPost.user_id == current_user.id)
        .order_by(BlogPost.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        HistoryPostSummary(
            id              = p.id,
            topic           = p.topic,
            word_count      = p.word_count or 0,
            image_count     = len(p.images) if p.images else 0,
            created_at      = p.created_at.isoformat(),
            content_preview = (p.content[:300] + "…") if len(p.content) > 300 else p.content,
        )
        for p in posts
    ]


@app.get("/history/{post_id}")
def get_history_post(
    post_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return a single blog post. 404 if not found, 403 if it belongs to another user."""
    post = db.query(BlogPost).filter(BlogPost.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return HistoryPostFull(
        id         = post.id,
        topic      = post.topic,
        content    = post.content,
        images     = post.images or [],
        word_count = post.word_count or 0,
        created_at = post.created_at.isoformat(),
    )


@app.get("/research/stream")
def research_stream(
    topic: str,
    current_user: User = Depends(get_current_user),
):
    """SSE endpoint — streams agent progress events then the final result."""
    q: queue.Queue = queue.Queue()

    def on_progress(stage: str, msg: str = ""):
        q.put({"stage": stage, "msg": msg})

    def run():
        try:
            result = run_research_pipeline(topic, on_progress=on_progress)

            # Save to Supabase/PostgreSQL — open a new session (thread-safe)
            db = SessionLocal()
            try:
                post = BlogPost(
                    user_id        = current_user.id,
                    topic          = result["topic"],
                    content        = result["content"],
                    images         = result.get("images", []),
                    word_count     = result.get("word_count", 0),
                    chroma_post_id = result.get("post_id"),
                )
                db.add(post)
                db.commit()
                db.refresh(post)
                result["db_post_id"] = post.id
                print(f"[DB] Blog post saved — id: {post.id}, user: {current_user.id}")
            except Exception as db_err:
                db.rollback()
                print(f"[DB] WARNING: Could not save post: {db_err}")
            finally:
                db.close()

            q.put({"stage": "done", "result": result})
        except Exception as e:
            q.put({"stage": "error", "msg": str(e)})

    threading.Thread(target=run, daemon=True).start()

    def generate():
        while True:
            event = q.get()
            yield f"data: {json.dumps(event)}\n\n"
            if event["stage"] in ("done", "error"):
                break

    return StreamingResponse(generate(), media_type="text/event-stream")


@app.post("/research")
def research(
    request:      ResearchRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Run the full multi-agent pipeline.
    Requires: Bearer token (login first via POST /auth/login).
    Returns: blog content + image URLs + word count.
    Time: ~60-90 seconds.
    Cost: ~$0.03 per run.
    """
    try:
        result = run_research_pipeline(request.topic)
        return result
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        with open("error_debug.txt", "w", encoding="utf-8") as f:
            f.write(tb)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/export")
async def export(request: ExportRequest):
    """
    Export blog post as PDF or Word document.
    """
    if not request.topic or not request.content:
        raise HTTPException(
            status_code=400,
            detail="topic and content are required"
        )

    try:
        if request.format == "pdf":
            path = export_to_pdf(
                topic=request.topic,
                content=request.content,
                image_url=request.image_url or None,
            )
            media_type = "application/pdf"
        else:
            path = export_to_word(
                topic=request.topic,
                content=request.content,
                image_url=request.image_url or None,
            )
            media_type = (
                "application/vnd.openxmlformats-"
                "officedocument.wordprocessingml.document"
            )

        return FileResponse(
            path=path,
            media_type=media_type,
            filename=os.path.basename(path),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
