# Installation

## Prerequisites

- Docker Desktop or Docker Engine
- Python 3.11+ for local tests
- Ollama installed and running
- Git

## Clone and configure

```bash
git clone https://github.com/adm-l/GroundedRAG.git
cd GroundedRAG
cp .env.example .env
```

## Download models

```bash
ollama pull nomic-embed-text
ollama pull qwen3:4b
ollama list
```

Ollama normally listens on port 11434. In Docker Desktop on macOS, the API container reaches the host service at http://host.docker.internal:11434.

## Start services

```bash
docker compose up --build
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- PostgreSQL host port: 5433

Stop with Ctrl+C or docker compose down. Database data remains in the named volume. To delete it as well, run docker compose down -v; this is destructive.

## Run locally (optional)

Start PostgreSQL with pgvector first, then:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL='postgresql://rag:rag_dev_password@localhost:5433/ragdb'
export OLLAMA_BASE_URL='http://localhost:11434'
uvicorn app.main:app --reload
```

## Health checks

```bash
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

## Upload, index, search, ask

```bash
cat > sample.txt <<'EOF'
Our backend uses Go for high-performance services.
PostgreSQL stores transactional data.
Redis provides caching and rate limiting.
Kafka handles asynchronous event processing.
EOF
curl -X POST http://localhost:8000/documents -F 'file=@sample.txt;type=text/plain'
```

Copy the returned id into the process route:

```bash
curl -X POST http://localhost:8000/documents/REPLACE_WITH_ID/process
curl -X POST http://localhost:8000/search -H 'Content-Type: application/json' -d '{"question":"Which technology handles caching?","top_k":3}'
curl -X POST http://localhost:8000/ask -H 'Content-Type: application/json' -d '{"question":"Which technology handles caching?","top_k":3}'
```

See API.md for request and response details.
