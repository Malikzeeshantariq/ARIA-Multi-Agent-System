import os
from crewai import Crew, Task, Process
from dotenv import load_dotenv
from .research_agent import run_research
from .writer_agent import create_writer_agent
from .image_agent import generate_images_for_blog
from .memory_agent import (
    save_blog_post,
    track_topic,
    search_similar_posts,
    search_documents,
)

load_dotenv()


def run_research_pipeline(topic: str, on_progress=None) -> dict:
    """
    Main pipeline — runs all agents in sequence.

    ✅ Research  → OpenAI Responses API (built-in web search, no Serper needed)
    ✅ Writing   → crewai Writer Agent (gpt-4o-mini)
    ✅ Images    → GPT Image 2 ($0.005/image)
    ✅ Export    → fpdf2 / python-docx (local, no API)

    on_progress(stage, msg) is called at each agent handoff when provided.
    """

    def _emit(stage, msg=""):
        if on_progress:
            on_progress(stage, msg)

    print(f"\n[START] Starting Multi-Agent Pipeline for: {topic}")
    print("=" * 60)

    # ── Step 1: Memory — track topic + fetch context ───────────
    print("[MEMORY] Tracking topic and fetching context...")
    track_topic(topic)

    # Search document base for relevant content
    doc_context = search_documents(topic, n_results=5)
    if doc_context:
        print(f"[MEMORY] Found document context ({len(doc_context.split())} words)")

    # Find similar past posts (shown in result, not injected into prompt)
    similar_posts = search_similar_posts(topic, n_results=3)
    if similar_posts:
        print(f"[MEMORY] Found {len(similar_posts)} similar past posts")

    # ── Step 2: Research via OpenAI Responses API ──────────────
    _emit("research", "Searching the web…")
    print("\n[SEARCH] Research Agent starting web search...")
    research_output = run_research(topic, document_context=doc_context)

    # ── Step 3: Write blog post via crewai Writer Agent ────────
    _emit("writing", "Writing blog post…")
    print("[INIT] Initializing Writer Agent...")
    writer = create_writer_agent()

    write_task = Task(
        description=(
            f"Using the research below, write a complete blog post about: '{topic}'\n\n"
            f"--- RESEARCH ---\n{research_output}\n--- END RESEARCH ---\n\n"
            "The blog post MUST follow this exact structure:\n\n"
            "# [Compelling Title Here]\n\n"
            "## Introduction\n"
            "(Hook the reader in 2-3 sentences)\n\n"
            "## [Section 1 — Key Concepts]\n"
            "(Explain the fundamentals)\n\n"
            "## [Section 2 — Current Trends]\n"
            "(Latest developments and data)\n\n"
            "## [Section 3 — Real World Impact]\n"
            "(Examples and case studies)\n\n"
            "## [Section 4 — Future Outlook]\n"
            "(What's coming next)\n\n"
            "## Key Takeaways\n"
            "- Takeaway 1\n"
            "- Takeaway 2\n"
            "- Takeaway 3\n\n"
            "Target: 800-1000 words. Tone: informative but engaging."
        ),
        agent=writer,
        expected_output=(
            "A complete, well-formatted blog post with title, "
            "introduction, 4 sections, and key takeaways."
        ),
    )

    crew = Crew(
        agents=[writer],
        tasks=[write_task],
        process=Process.sequential,   # ✅ crewai 1.x syntax
        verbose=False,                # disabled: rich output breaks Windows cp1252
    )

    result = crew.kickoff()

    # ✅ crewai 1.x — result is CrewOutput object, use .raw for string
    content = result.raw if hasattr(result, "raw") else str(result)

    # ── Generate images ────────────────────────────────────────
    _emit("images", "Generating images…")
    print("\n[IMAGE] Image Agent generating visuals...")
    sections = [
        f"Key aspects and concepts of {topic}",
        f"Future trends and developments in {topic}",
    ]
    images = generate_images_for_blog(topic, sections)

    # ── Save to ChromaDB memory ────────────────────────────────
    print("\n[MEMORY] Saving blog post to memory...")
    post_id = save_blog_post(topic, content, image_count=len(images))

    print("\n[DONE] Pipeline complete!")
    print("=" * 60)

    return {
        "topic":        topic,
        "content":      content,
        "images":       images,
        "image_count":  len(images),
        "word_count":   len(content.split()),
        "post_id":      post_id,
        "similar_posts": similar_posts,   # previously generated similar posts
    }
