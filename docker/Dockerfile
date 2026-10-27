# ── Etapa 1: Builder ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements-cloud.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements-cloud.txt

# ── Etapa 2: Runtime ──────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copiar dependencias compiladas desde el builder
COPY --from=builder /install /usr/local

# Copiar directorios del proyecto
COPY backend/ ./backend/
COPY frontend/ ./frontend/
COPY Informacion_docling_rag/ ./Informacion_docling_rag/
COPY .env.example ./.env

# Crear directorios de persistencia pericial
RUN mkdir -p RAG/inputs RAG/articulos logs

ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV CORS_ORIGINS=*
ENV LOG_LEVEL=INFO

EXPOSE 8000

# Verificación de salud integrada
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
