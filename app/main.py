import hashlib
import logging
import uuid
from contextlib import asynccontextmanager
from typing import Annotated
from uuid import UUID

import psycopg
from fastapi import FastAPI, File, HTTPException, Response, UploadFile
from pgvector import Vector
from pgvector.psycopg import register_vector
from pydantic import BaseModel, Field

from app.chunking import split_text
from app.config import CHUNK_OVERLAP, CHUNK_SIZE, MAX_COSINE_DISTANCE, MAX_DOCUMENT_BYTES
from app.db import get_connection, init_db
from app.embeddings import generate_embedding
from app.llm import generate_answer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("groundedrag")


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="GroundedRAG API", description="Document ingestion, semantic retrieval, and context-grounded Q&A.", version="0.1.0", lifespan=lifespan)


class DocumentResponse(BaseModel):
    id: UUID
    filename: str
    content_type: str
    sha256: str
    status: str
    created_at: str | None = None


class SearchRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


class SearchSource(BaseModel):
    document_id: UUID
    filename: str
    chunk_index: int
    content: str
    distance: float


class SearchResponse(BaseModel):
    question: str
    results: list[SearchSource]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


class AskResponse(BaseModel):
    question: str
    answer: str
    sources: list[SearchSource]


def _search(question: str, top_k: int) -> list[SearchSource]:
    try:
        query_embedding = Vector(generate_embedding(question))
    except RuntimeError as exc:
        logger.warning("Embedding generation failed: %s", exc)
        raise HTTPException(502, "Could not generate the question embedding") from exc
    try:
        with get_connection() as connection:
            register_vector(connection)
            rows = connection.execute("""
                WITH candidates AS (
                    SELECT dc.document_id, d.filename, dc.chunk_index, dc.content,
                           dc.embedding <=> %s AS distance
                    FROM document_chunks AS dc
                    JOIN documents AS d ON d.id = dc.document_id
                    WHERE d.status = 'indexed' AND dc.embedding IS NOT NULL
                ),
                ranked AS (
                    SELECT candidates.*,
                           ROW_NUMBER() OVER (
                               PARTITION BY content
                               ORDER BY distance, document_id
                           ) AS duplicate_rank
                    FROM candidates
                    WHERE distance <= %s
                )
                SELECT document_id, filename, chunk_index, content, distance
                FROM ranked
                WHERE duplicate_rank = 1
                ORDER BY distance
                LIMIT %s
            """, (query_embedding, MAX_COSINE_DISTANCE, top_k)).fetchall()
    except psycopg.Error as exc:
        logger.exception("Retrieval database error")
        raise HTTPException(503, "Could not retrieve relevant document chunks") from exc
    return [SearchSource(document_id=r[0], filename=r[1], chunk_index=r[2], content=r[3], distance=float(r[4])) for r in rows]


@app.get("/health/live")
def health_live():
    return {"status": "ok"}


@app.get("/health/ready")
def health_ready():
    try:
        with get_connection() as connection:
            connection.execute("SELECT 1")
    except psycopg.Error as exc:
        raise HTTPException(503, "Database is not ready") from exc
    return {"status": "ready", "database": "ok"}


@app.post("/documents", response_model=DocumentResponse, status_code=201)
async def upload_document(file: Annotated[UploadFile, File()], response: Response):
    filename = file.filename or "upload.txt"
    if not filename.lower().endswith((".txt", ".md")):
        raise HTTPException(415, "Only .txt and .md files are supported")
    raw = await file.read(MAX_DOCUMENT_BYTES + 1)
    if len(raw) > MAX_DOCUMENT_BYTES:
        raise HTTPException(413, f"File exceeds {MAX_DOCUMENT_BYTES} bytes")
    try:
        content = raw.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "Document must be UTF-8 encoded") from exc
    if not content:
        raise HTTPException(400, "Document is empty")
    digest = hashlib.sha256(raw).hexdigest()
    try:
        with get_connection() as connection:
            existing = connection.execute("""
                SELECT id, filename, content_type, sha256, status, created_at
                FROM documents
                WHERE sha256 = %s
                ORDER BY created_at
                LIMIT 1
            """, (digest,)).fetchone()
            if existing:
                response.status_code = 200
                row = existing
            else:
                row = connection.execute("""
                    INSERT INTO documents (id, filename, content_type, sha256, extracted_text)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, filename, content_type, sha256, status, created_at
                """, (uuid.uuid4(), filename, file.content_type or "text/plain", digest, content)).fetchone()
    except psycopg.Error as exc:
        logger.exception("Document upload database error")
        raise HTTPException(503, "Could not save document") from exc
    return DocumentResponse(id=row[0], filename=row[1], content_type=row[2], sha256=row[3], status=row[4], created_at=row[5].isoformat())


@app.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: UUID):
    try:
        with get_connection() as connection:
            row = connection.execute("SELECT id, filename, content_type, sha256, status, created_at FROM documents WHERE id = %s", (document_id,)).fetchone()
    except psycopg.Error as exc:
        raise HTTPException(503, "Could not read document metadata") from exc
    if not row:
        raise HTTPException(404, "Document not found")
    return DocumentResponse(id=row[0], filename=row[1], content_type=row[2], sha256=row[3], status=row[4], created_at=row[5].isoformat())


@app.post("/documents/{document_id}/process")
def process_document(document_id: UUID):
    try:
        with get_connection() as connection:
            row = connection.execute("SELECT extracted_text FROM documents WHERE id = %s", (document_id,)).fetchone()
            if not row:
                raise HTTPException(404, "Document not found")
            connection.execute("UPDATE documents SET status = 'processing', updated_at = now() WHERE id = %s", (document_id,))
    except psycopg.Error as exc:
        raise HTTPException(503, "Could not load document") from exc
    chunks = split_text(row[0], CHUNK_SIZE, CHUNK_OVERLAP)
    if not chunks:
        raise HTTPException(400, "Document contains no indexable text")
    try:
        embeddings = [generate_embedding(chunk) for chunk in chunks]
        with get_connection() as connection:
            register_vector(connection)
            connection.execute("DELETE FROM document_chunks WHERE document_id = %s", (document_id,))
            for index, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                connection.execute("INSERT INTO document_chunks (document_id, chunk_index, content, embedding) VALUES (%s, %s, %s, %s)", (document_id, index, chunk, Vector(embedding)))
            connection.execute("UPDATE documents SET status = 'indexed', updated_at = now() WHERE id = %s", (document_id,))
    except (RuntimeError, psycopg.Error) as exc:
        logger.exception("Document indexing failed")
        try:
            with get_connection() as connection:
                connection.execute("UPDATE documents SET status = 'failed', updated_at = now() WHERE id = %s", (document_id,))
        except psycopg.Error:
            logger.exception("Could not mark document as failed")
        raise HTTPException(502, "Document indexing failed; check Ollama and database logs") from exc
    return {"document_id": str(document_id), "status": "indexed", "chunks_indexed": len(chunks)}


@app.post("/search", response_model=SearchResponse)
def semantic_search(request: SearchRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(400, "Question must not be empty")
    return SearchResponse(question=question, results=_search(question, request.top_k))


@app.post("/ask", response_model=AskResponse)
def ask_question(request: AskRequest):
    question = request.question.strip()
    if not question:
        raise HTTPException(400, "Question must not be empty")
    sources = _search(question, request.top_k)
    if not sources:
        return AskResponse(question=question, answer="I could not find relevant information in the indexed documents.", sources=[])
    context = "\n\n".join(f"Source: {source.filename}\n{source.content}" for source in sources)
    try:
        answer = generate_answer(question, context)
    except RuntimeError as exc:
        logger.warning("Answer generation failed: %s", exc)
        raise HTTPException(502, "Could not generate an answer using Ollama") from exc
    return AskResponse(question=question, answer=answer, sources=sources)
