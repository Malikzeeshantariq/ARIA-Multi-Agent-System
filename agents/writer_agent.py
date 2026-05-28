from crewai import Agent
from dotenv import load_dotenv

load_dotenv()


def create_writer_agent() -> Agent:
    """
    Writer Agent — takes research summary and writes
    a complete, well-structured blog post.
    ✅ Compatible with crewai 1.x
    """

    agent = Agent(
        role="Expert Content Writer",
        goal=(
            "Write a high-quality, engaging, and well-structured blog post "
            "based on the research provided. The post should be informative, "
            "easy to read, and ready to publish."
        ),
        backstory=(
            "You are a professional content writer and journalist with expertise "
            "in making complex topics accessible and engaging. You write compelling "
            "blog posts that are SEO-friendly, well-structured with clear headings, "
            "and always deliver real value to the reader."
        ),
        verbose=False,
        allow_delegation=False,
        max_iter=3,
    )

    return agent
