# ───────────────────────── Base Image ───────────────────────── #
FROM python:3.12-slim AS base

# System deps for PDF processing / OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ───────────────────────── Dependencies ───────────────────────── #
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ───────────────────────── Application ───────────────────────── #
COPY backend/ ./backend/

# Create data directory for SQLite
RUN mkdir -p /app/data

# Default env vars
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV DATABASE_PATH=/app/data/database.db

EXPOSE 8000

# ───────────────────────── Run ───────────────────────── #
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
