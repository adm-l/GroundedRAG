# Database

PostgreSQL 16 with pgvector is provided by the pgvector/pgvector:pg16 image.

## Tables

### documents

| Column | Type | Notes |
|---|---|---|
| id | UUID | Primary key |
| filename | TEXT | Original filename metadata |
| content_type | TEXT | Client MIME type or default |
| sha256 | TEXT | Hash of uploaded bytes |
| extracted_text | TEXT | UTF-8 source text |
| status | TEXT | uploaded, processing, indexed, failed |
| created_at | TIMESTAMPTZ | Created timestamp |
| updated_at | TIMESTAMPTZ | Status update timestamp |

### document_chunks

| Column | Type | Notes |
|---|---|---|
| id | BIGSERIAL | Primary key |
| document_id | UUID | FK, cascade delete |
| chunk_index | INTEGER | Zero-based position |
| content | TEXT | Chunk text |
| embedding | vector(768) | Embedding vector |
| created_at | TIMESTAMPTZ | Created timestamp |

Unique constraint: document_id plus chunk_index. HNSW index uses vector_cosine_ops. Search orders by the pgvector cosine-distance operator; lower distance indicates greater similarity.

The schema fixes the vector column at 768 dimensions. If the embedding model changes dimension, update schema/migrations and configuration together; changing an environment variable does not alter an existing column.

For development backup:

```bash
docker compose exec -T db pg_dump -U rag ragdb > backup.sql
```

Startup DDL is for development. Production should use versioned migrations, least-privilege roles, backups, and restore drills.
