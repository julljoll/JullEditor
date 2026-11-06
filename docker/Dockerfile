# ── Etapa 0: Build del sitio Astro ────────────────────────────────────────────
FROM node:24-bookworm-slim AS astro-builder

WORKDIR /workspace
WORKDIR /workspace/blog
COPY blog/package.json blog/package-lock.json ./
RUN npm ci --include=optional --workspaces=false
WORKDIR /workspace
COPY blog/ ./blog/
WORKDIR /workspace/blog
RUN node ./node_modules/astro/bin/astro.mjs build

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

# Runtime Node.js para el servidor SSR de Astro.
COPY --from=astro-builder /usr/local/bin/node /usr/local/bin/node

# Copiar dependencias compiladas desde el builder
COPY --from=builder /install /usr/local

# Copiar backend, corpus y salida de Astro.
COPY backend/ ./backend/
COPY --from=astro-builder /workspace/blog/package.json ./blog/package.json
COPY --from=astro-builder /workspace/blog/node_modules ./blog/node_modules
COPY --from=astro-builder /workspace/blog/dist ./blog/dist
COPY Informacion_docling_rag/ ./Informacion_docling_rag/
COPY .env.example ./.env
COPY docker/start.py ./docker/start.py

# Crear directorios de persistencia pericial
RUN mkdir -p "Articulos Generados/astro_ready" RAG/inputs RAG/articulos logs

ENV PYTHONUNBUFFERED=1
ENV APP_HOST=0.0.0.0
ENV APP_PORT=8000
ENV HOST=0.0.0.0
ENV PORT=3000
ENV BACKEND_API_URL=http://127.0.0.1:8000
ENV ASTRO_BASE_URL=http://localhost
ENV OLLAMA_BASE_URL=http://ollama:11434
ENV CORS_ORIGINS=*
ENV LOG_LEVEL=INFO

EXPOSE 3000 8000

# Verificación de salud integrada
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["python", "docker/start.py"]
