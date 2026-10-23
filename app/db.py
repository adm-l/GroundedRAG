import psycopg
from pgvector.psycopg import register_vector
from app.config import DATABASE_URL


def get_connection():
    return psycopg.connect(DATABASE_URL)


def init_db() -> None:
    with get_connection() as connection:
        connection.execute("CREATE EXTENSION IF NOT EXISTS vector")
        connection.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id UUID PRIMARY KEY, filename TEXT NOT NULL, content_type TEXT NOT NULL,
                sha256 TEXT NOT NULL, extracted_text TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'uploaded' CHECK (status IN ('uploaded','processing','indexed','failed')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)
        connection.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id BIGSERIAL PRIMARY KEY,
                document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
                chunk_index INTEGER NOT NULL, content TEXT NOT NULL, embedding vector(768),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now(), UNIQUE(document_id, chunk_index)
            )
        """)
        connection.execute("CREATE INDEX IF NOT EXISTS document_chunks_document_id_idx ON document_chunks(document_id)")
        connection.execute("CREATE INDEX IF NOT EXISTS document_chunks_embedding_hnsw_idx ON document_chunks USING hnsw (embedding vector_cosine_ops)")
        register_vector(connection)
