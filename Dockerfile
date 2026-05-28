FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ChromaDB persistent storage — mount a volume here in production
# Railway: set CHROMA_PATH=/data/chroma and mount volume at /data
RUN mkdir -p /data/chroma

EXPOSE 8000

# Frontend is deployed separately on Streamlit Cloud.
# Railway auto-sets DATABASE_URL when PostgreSQL plugin is added.
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
