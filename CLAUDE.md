# ARIA — Multi-Agent AI Research System
## Claude Code Guide

This file tells Claude Code exactly how this project works.

## Project Overview
ARIA uses 5 AI agents to research any topic and produce a complete
blog post with images. User types one topic → gets full article in ~90s.

## Architecture
```
User Topic
    ↓
Orchestrator (orchestrator.py)
    ↓
Research Agent  → OpenAI Responses API (built-in web search — no Serper needed)
Writer Agent    → GPT-4o mini via crewai (blog writing)
Image Agent     → GPT Image 2 (image generation — $0.005/image)
Export Agent    → fpdf2 / python-docx (PDF + Word, local)
    ↓
FastAPI (api/main.py) ← Streamlit (frontend/app.py)
```

## File Map
- `agents/orchestrator.py`   — connects all agents, main pipeline
- `agents/research_agent.py` — web search via OpenAI Responses API
- `agents/writer_agent.py`   — blog post writing via crewai
- `agents/image_agent.py`    — GPT Image 2 image generation
- `agents/export_agent.py`   — PDF and Word export
- `agents/memory_agent.py`   — ChromaDB memory (posts, topics, document base)
- `api/main.py`              — FastAPI REST backend
- `api/auth.py`              — JWT auth endpoints (register, login, me, logout)
- `database/connection.py`   — SQLAlchemy engine + get_db dependency
- `database/models.py`       — User model (PostgreSQL)
- `frontend/app.py`          — Streamlit UI with login page (ARIA-themed)
- `.env`                     — API keys + DB URL (never commit this)
- `chroma_data/`             — ChromaDB persistent storage (auto-created, do not delete)

## Key Libraries & Versions
- crewai==1.14.5          (uses Process.sequential, verbose=True, result.raw)
- openai==2.37.0          (Responses API + Images API)
- chromadb==0.6.3         (vector DB — 3 collections: blog_posts, user_topics, document_base)
- pydantic==2.13.4        (use @field_validator not @validator)
- fastapi==0.136.1
- streamlit==1.57.0

## API Keys Required
```
OPENAI_API_KEY   = from platform.openai.com   ← ONLY key needed now!
```
> SERPER_API_KEY is no longer required — web search is built into OpenAI Responses API.

## Common Tasks for Claude Code

### Run the project
```bash
# Terminal 1
uvicorn api.main:app --reload --port 8000

# Terminal 2
streamlit run frontend/app.py
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Test the API
```bash
curl -X POST http://localhost:8000/research \
  -H "Content-Type: application/json" \
  -d '{"topic": "Future of AI"}'
```

### Add a new agent
1. Create `agents/my_agent.py` with a function for your agent
2. Add a Task in `agents/orchestrator.py`
3. Add agent to the Crew list (if crewai-based) or call directly
4. Export from `agents/__init__.py`

## Agent Patterns

### Research Agent — OpenAI Responses API
```python
from openai import OpenAI
client = OpenAI()

response = client.responses.create(
    model="gpt-4o-mini",
    instructions="You are a research analyst...",
    input=f"Research: {topic}",
    tools=[{"type": "web_search_preview"}],  # built-in, FREE
)
text = response.output_text
```

### Writer Agent — crewai 1.x patterns
```python
from crewai import Crew, Task, Process

crew = Crew(
    agents=[writer],
    tasks=[write_task],
    process=Process.sequential,  # NOT verbose=2
    verbose=False,               # verbose=True breaks Windows cp1252
)
result = crew.kickoff()
content = result.raw  # NOT str(result)
```

### Image Agent — GPT Image 2
```python
response = client.images.generate(
    model="gpt-image-2",
    prompt=enhanced_prompt,
    size="1024x1024",
    quality="low",      # $0.005/image | medium=$0.053 | high=$0.211
)
# GPT Image 2 returns b64_json by default (no URL expiry issue)
b64 = response.data[0].b64_json
url = f"data:image/png;base64,{b64}"
```

## Cost per Run
| Step | Cost |
|---|---|
| Research (Responses API) | ~$0.005 |
| Writing (GPT-4o mini) | ~$0.010 |
| Images × 3 (GPT Image 2 low) | ~$0.015 |
| **Total** | **~$0.03** |

With $10 → ~333 complete runs.

## Environment Variables
```
OPENAI_API_KEY   = from platform.openai.com       (required)
OPENAI_MODEL     = gpt-4o-mini                    (writer model)
RESEARCH_MODEL   = gpt-4o-mini                    (research model)
IMAGE_MODEL      = gpt-image-2                    (image model)
IMAGE_SIZE       = 1024x1024
IMAGE_QUALITY    = low                            (low/medium/high)
PYTHONUTF8       = 1                              (Windows fix)

DATABASE_URL     = postgresql://...               (required for auth)
JWT_SECRET       = random 32-char string          (required for auth)
ACCESS_TOKEN_EXPIRE_MINUTES = 60                  (optional, default 60)
CHROMA_PATH      = /data/chroma                   (optional, default ./chroma_data)
```

## Auth Flow
```
POST /auth/register  {email, password, full_name}  → {access_token, user}
POST /auth/login     form: username+password        → {access_token, user}
GET  /auth/me        Bearer token                   → {id, email, full_name}
POST /research       Bearer token required
```

## Deployment (Railway)
1. Create new project → Deploy from GitHub
2. Add PostgreSQL plugin → DATABASE_URL set automatically
3. Add volume mounted at `/data` → set CHROMA_PATH=/data/chroma
4. Set env vars: OPENAI_API_KEY, JWT_SECRET, CHROMA_PATH
5. Streamlit frontend → deploy separately on Streamlit Cloud
   - Set API_URL to your Railway backend URL

## ChromaDB Memory Features
Three persistent collections stored in `./chroma_data/`:

| Collection | What it stores | Key functions |
|---|---|---|
| `blog_posts` | Every generated blog post + metadata | `save_blog_post`, `search_similar_posts`, `get_all_posts` |
| `user_topics` | Search history with counts | `track_topic`, `get_favorite_topics` |
| `document_base` | User-uploaded docs chunked into 400-word pieces | `add_document`, `search_documents`, `list_documents` |

### ChromaDB API Endpoints
- `GET  /memory/stats`        — collection counts
- `GET  /memory/posts`        — all saved blog posts
- `GET  /memory/topics`       — top searched topics
- `GET  /memory/documents`    — list uploaded docs
- `POST /memory/documents`    — add text to doc base `{text, source}`
- `GET  /memory/search?q=...` — semantic search over doc base

## Known Issues / Notes
- DALL-E 2 and DALL-E 3 were removed from OpenAI API on May 12, 2026 — use GPT Image 2
- GPT Image 2 returns `b64_json` by default — no URL expiry issue (unlike old DALL-E)
- crewai SerperDevTool is no longer used — SERPER_API_KEY not needed
- pydantic 2.x: use @field_validator + @classmethod (not @validator)
- Export PDF uses Helvetica not Arial (fpdf2 2.8.x built-in font)
- verbose=False in Crew — rich output breaks Windows cp1252 terminal
- PYTHONUTF8=1 must be set in environment for Windows UTF-8 support
- ChromaDB `chroma_data/` folder is created automatically on first run
