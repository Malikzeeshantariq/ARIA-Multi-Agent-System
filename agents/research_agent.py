import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ✅ Uses OpenAI Responses API with built-in web search
# No Serper API key needed — web search is FREE and built-in!
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def run_research(topic: str, document_context: str = "") -> str:
    """
    Research a topic using OpenAI Responses API with built-in web search.

    Args:
        topic:            The topic to research
        document_context: Optional text from ChromaDB document base.
                          If provided, the model uses it as additional context
                          before searching the web.

    Override model via environment variable:
        RESEARCH_MODEL (default: gpt-4o-mini)
    """
    print(f"[RESEARCH] Searching web for: {topic}")

    model = os.getenv("RESEARCH_MODEL", "gpt-4o-mini")

    # Prepend local document context if available
    doc_section = ""
    if document_context:
        doc_section = (
            "You also have access to the following content from the user's "
            "uploaded document base. Use it to enrich your research:\n\n"
            f"{document_context}\n\n"
            "---\n\n"
        )
        print(f"[RESEARCH] Including {len(document_context.split())} words from document base")

    response = client.responses.create(
        model=model,
        instructions=(
            "You are an expert research analyst with 10 years of experience. "
            "You find the most relevant and up-to-date information on any topic. "
            "You always verify facts and cite your sources clearly."
        ),
        input=(
            f"{doc_section}"
            f"Research this topic thoroughly: '{topic}'\n\n"
            "Your research must include:\n"
            "1. Key facts and current statistics\n"
            "2. Recent developments and trends\n"
            "3. Expert opinions or notable quotes\n"
            "4. Real-world examples or case studies\n"
            "5. Source URLs for all major claims\n\n"
            "Provide a well-organized research summary."
        ),
        tools=[{"type": "web_search_preview"}],
    )

    research_text = response.output_text
    print(f"[RESEARCH] Done — {len(research_text.split())} words collected")
    return research_text
