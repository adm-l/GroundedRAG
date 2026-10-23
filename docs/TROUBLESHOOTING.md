# Troubleshooting

## Ollama connection errors

Confirm Ollama works on the host with curl http://localhost:11434/api/tags. In Docker Desktop, configure OLLAMA_BASE_URL as http://host.docker.internal:11434, not localhost. Pull both configured model tags and restart the API after changing environment variables.

## PostgreSQL connection errors

Run docker compose ps and docker compose logs db. Host tools use port 5433 by default; the API container uses db:5432. Wait for the database health check.

## Vector dimension mismatch

The schema expects 768 dimensions. Confirm the embedding model returns 768 values. Updating an environment variable does not migrate the existing vector column.

## pgvector operator/type errors

Register pgvector on each psycopg connection used for vector values and pass a pgvector Vector object to vector operators. Query and stored vector dimensions must match.

## 502 response

Inspect docker compose logs -f api. Check Ollama availability, installed model names, and available machine memory. Local inference can be slow on machines with limited RAM.

## Reset development data

Warning: this removes all indexed documents and vectors.

```bash
docker compose down -v
docker compose up --build
```
