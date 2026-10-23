# Configuration

Values are read from environment variables. Compose loads a local .env file when present.

| Variable | Default | Purpose |
|---|---|---|
| DATABASE_URL | local PostgreSQL URL | Connection string |
| POSTGRES_DB | ragdb | Compose database |
| POSTGRES_USER | rag | Compose database user |
| POSTGRES_PASSWORD | rag_dev_password | Development-only password |
| POSTGRES_HOST_PORT | 5433 | Host-mapped PostgreSQL port |
| OLLAMA_BASE_URL | host.docker.internal:11434 in Compose | Ollama base URL |
| OLLAMA_EMBED_MODEL | nomic-embed-text | Embedding model |
| OLLAMA_CHAT_MODEL | qwen3:4b | Chat model |
| EMBEDDING_DIMENSIONS | 768 | Expected vector length |
| CHUNK_SIZE | 1000 | Maximum characters per chunk |
| CHUNK_OVERLAP | 150 | Overlap between chunks |
| MAX_DOCUMENT_BYTES | 2097152 | Upload byte limit |
| MAX_COSINE_DISTANCE | 0.45 | Initial maximum cosine distance for a retrieved chunk |

MAX_COSINE_DISTANCE is a configurable heuristic, not a probability or universally correct cutoff. Lower cosine distance means closer vectors. The default 0.45 is an initial development value; evaluate it against representative answerable and unanswerable questions before relying on it. Set a value from 0.0 to 2.0. A lower value returns fewer chunks; a higher value admits less-similar chunks.

The database schema currently fixes vector(768). Changing EMBEDDING_DIMENSIONS alone does not migrate an existing database. Never commit a real .env file, passwords, tokens, or private documents.
