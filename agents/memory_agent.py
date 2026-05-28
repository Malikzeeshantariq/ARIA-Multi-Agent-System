from __future__ import annotations

import hashlib
import os
from datetime import datetime

import chromadb
from dotenv import load_dotenv

load_dotenv()

# ── Persistent ChromaDB client ─────────────────────────────────
# Path is configurable via CHROMA_PATH env var.
# - Local dev:   ./chroma_data   (default)
# - Railway:     /data/chroma    (set CHROMA_PATH=/data/chroma)
# - Docker:      mount volume at CHROMA_PATH location

_client: chromadb.PersistentClient | None = None


def _get_client() -> chromadb.PersistentClient:
    global _client
    if _client is None:
        chroma_path = os.getenv("CHROMA_PATH", "./chroma_data")
        os.makedirs(chroma_path, exist_ok=True)
        _client = chromadb.PersistentClient(path=chroma_path)
    return _client


def _blog_col():
    return _get_client().get_or_create_collection("blog_posts")


def _topics_col():
    return _get_client().get_or_create_collection("user_topics")


def _docs_col():
    return _get_client().get_or_create_collection("document_base")


# ─────────────────────────────────────────────────────────────
# Feature 1 — Previous Blog Posts Memory
# ─────────────────────────────────────────────────────────────

def save_blog_post(topic: str, content: str, image_count: int = 0) -> str:
    """
    Save a generated blog post to ChromaDB memory.
    Returns the post ID.
    """
    post_id = hashlib.md5(
        f"{topic}{datetime.now().isoformat()}".encode()
    ).hexdigest()[:12]

    _blog_col().add(
        documents=[content],
        metadatas=[{
            "topic":       topic,
            "word_count":  len(content.split()),
            "image_count": image_count,
            "created_at":  datetime.now().isoformat(),
        }],
        ids=[post_id],
    )
    print(f"[MEMORY] Blog post saved — id: {post_id}, topic: {topic}")
    return post_id


def search_similar_posts(topic: str, n_results: int = 3) -> list[dict]:
    """
    Find previously generated posts similar to a given topic.
    Returns list of {topic, content_preview, word_count, created_at}.
    """
    col = _blog_col()
    if col.count() == 0:
        return []

    results = col.query(
        query_texts=[topic],
        n_results=min(n_results, col.count()),
    )

    posts = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        posts.append({
            "topic":           meta.get("topic", ""),
            "content_preview": doc[:400] + "…",
            "word_count":      meta.get("word_count", 0),
            "created_at":      meta.get("created_at", ""),
        })
    return posts


def get_all_posts(limit: int = 20) -> list[dict]:
    """Return all saved blog posts (most recent first)."""
    col = _blog_col()
    if col.count() == 0:
        return []

    result = col.get(include=["metadatas", "documents"])
    posts = []
    for i, meta in enumerate(result["metadatas"]):
        posts.append({
            "id":              result["ids"][i],
            "topic":           meta.get("topic", ""),
            "word_count":      meta.get("word_count", 0),
            "image_count":     meta.get("image_count", 0),
            "created_at":      meta.get("created_at", ""),
            "content_preview": result["documents"][i][:400] + "…",
        })

    posts.sort(key=lambda x: x["created_at"], reverse=True)
    return posts[:limit]


# ─────────────────────────────────────────────────────────────
# Feature 2 — User Favourite Topics Tracker
# ─────────────────────────────────────────────────────────────

def track_topic(topic: str) -> int:
    """
    Increment search count for a topic.
    Returns the new count.
    """
    col       = _topics_col()
    topic_id  = hashlib.md5(topic.lower().strip().encode()).hexdigest()[:12]
    existing  = col.get(ids=[topic_id])

    if existing["ids"]:
        count = existing["metadatas"][0].get("count", 1) + 1
        col.update(
            ids=[topic_id],
            metadatas=[{
                "topic":         topic,
                "count":         count,
                "last_searched": datetime.now().isoformat(),
            }],
        )
    else:
        count = 1
        col.add(
            documents=[topic],
            metadatas=[{
                "topic":         topic,
                "count":         1,
                "last_searched": datetime.now().isoformat(),
            }],
            ids=[topic_id],
        )

    print(f"[MEMORY] Topic tracked: '{topic}' (count={count})")
    return count


def get_favorite_topics(n: int = 10) -> list[dict]:
    """
    Return top-n most searched topics.
    Returns list of {topic, count, last_searched}.
    """
    col = _topics_col()
    if col.count() == 0:
        return []

    all_items = col.get(include=["metadatas"])
    topics = sorted(
        all_items["metadatas"],
        key=lambda x: x.get("count", 0),
        reverse=True,
    )
    return topics[:n]


# ─────────────────────────────────────────────────────────────
# Feature 3 — Document Base (RAG)
# ─────────────────────────────────────────────────────────────

def add_document(text: str, source: str, chunk_size: int = 400) -> int:
    """
    Chunk a document and store it in ChromaDB.
    Returns number of chunks added.

    Args:
        text:       Full text content of the document
        source:     Filename or label (e.g. "research_paper.pdf")
        chunk_size: Words per chunk (default 400)
    """
    words  = text.split()
    chunks = [
        " ".join(words[i: i + chunk_size])
        for i in range(0, len(words), chunk_size)
        if words[i: i + chunk_size]
    ]

    if not chunks:
        return 0

    col       = _docs_col()
    ids       = []
    metadatas = []

    for i, chunk in enumerate(chunks):
        chunk_id = hashlib.md5(f"{source}{i}".encode()).hexdigest()[:12]
        ids.append(chunk_id)
        metadatas.append({
            "source":      source,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "added_at":    datetime.now().isoformat(),
        })

    col.add(documents=chunks, metadatas=metadatas, ids=ids)
    print(f"[MEMORY] Document added: '{source}' — {len(chunks)} chunks")
    return len(chunks)


def search_documents(query: str, n_results: int = 5) -> str:
    """
    Semantic search over the document base.
    Returns relevant text chunks joined together, or "" if empty.
    """
    col = _docs_col()
    if col.count() == 0:
        return ""

    results = col.query(
        query_texts=[query],
        n_results=min(n_results, col.count()),
    )

    docs = results["documents"][0]
    if not docs:
        return ""

    sources = [m.get("source", "unknown") for m in results["metadatas"][0]]
    parts   = [f"[Source: {s}]\n{d}" for s, d in zip(sources, docs)]
    return "\n\n---\n\n".join(parts)


def list_documents() -> list[dict]:
    """Return unique document sources stored in the base."""
    col = _docs_col()
    if col.count() == 0:
        return []

    all_items = col.get(include=["metadatas"])
    seen: dict[str, dict] = {}
    for meta in all_items["metadatas"]:
        src = meta.get("source", "unknown")
        if src not in seen:
            seen[src] = {
                "source":       src,
                "total_chunks": meta.get("total_chunks", "?"),
                "added_at":     meta.get("added_at", ""),
            }
    return list(seen.values())


# ─────────────────────────────────────────────────────────────
# Stats
# ─────────────────────────────────────────────────────────────

def get_stats() -> dict:
    """Return counts for all three ChromaDB collections."""
    return {
        "blog_posts_saved":    _blog_col().count(),
        "topics_tracked":      _topics_col().count(),
        "document_chunks":     _docs_col().count(),
    }
