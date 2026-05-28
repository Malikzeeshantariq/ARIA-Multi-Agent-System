# ◈ ARIA — AI Research Intelligence Agent

> Multi-Agent system: one topic in → full blog post + images out in ~90 seconds.

---

## Quick Start

```bash
# 1. Install
pip install -r requirements.txt

# 2. Add your OpenAI key to .env
OPENAI_API_KEY=your_key
# No Serper key needed — web search is built into Responses API!

# 3. Run
uvicorn api.main:app --reload --port 8000
streamlit run frontend/app.py

# 4. Open
# App  → http://localhost:8501
# Docs → http://localhost:8000/docs
```

---

## Agents

| Agent | Role | Tool |
|---|---|---|
| Orchestrator | Controls pipeline | — |
| Research Agent | Web search | OpenAI Responses API (built-in search) |
| Writer Agent | Blog writing | GPT-4o mini via crewai |
| Image Agent | Visuals | GPT Image 2 ($0.005/image) |
| Export Agent | PDF + Word | fpdf2 / docx |

---

## Stack

`crewai 1.x` · `openai 2.x` · `fastapi` · `streamlit` · `docker`

---

## Cost per run: ~$0.02

| Step | Cost |
|---|---|
| Research (Responses API + web search) | ~$0.005 |
| Writing (GPT-4o mini) | ~$0.010 |
| Images × 3 (GPT Image 2 low) | ~$0.015 |
| **Total** | **~$0.03** |

> With $10 OpenAI credit → ~333 complete runs  
> (vs ~76 runs with old DALL-E 3 pricing)
