# API reference

Base URL: http://localhost:8000. Interactive documentation is at /docs.

## Health endpoints

- GET /health/live reports that the API process is running; it does not check dependencies.
- GET /health/ready executes a database query and returns 503 if PostgreSQL is unavailable.

## POST /documents

Multipart form field: file. Supports .txt and .md, UTF-8, non-empty content, maximum 2 MiB by default. A new document returns 201 with document ID, filename, content type, SHA-256, status, and creation time. If the exact same bytes (same SHA-256) were already uploaded, the API returns the existing document with status 200 instead of creating another document record.

Typical errors: 400 invalid or empty text, 413 too large, 415 unsupported extension, 503 database failure.

## GET /documents/{document_id}

Returns document metadata and status, or 404 if the UUID does not exist.

## POST /documents/{document_id}/process

Splits stored text, generates embeddings, and stores chunks. Returns document ID, indexed status, and chunk count. This operation is synchronous. Model or database failures return 502.

## POST /search

Request body example: {"question":"Which technology handles caching?","top_k":3}

Question length is 1–2000 characters; top_k is 1–10 and defaults to 3. Response contains question and results. Each result contains document ID, filename, chunk index, content, and cosine distance. Smaller distance means closer vectors; it is not a calibrated probability. Duplicate chunks are collapsed after whitespace normalization, with the closest match retained; this applies across duplicate document records too. Chunks with distance above MAX_COSINE_DISTANCE are filtered out.

## POST /ask

Uses the same request shape. Response contains question, generated answer, and sources. The prompt instructs the model to answer when context directly answers or clearly implies the answer, even when wording differs, and to abstain when context genuinely lacks the information. Prompt instructions cannot guarantee zero hallucinations. The default retrieval cutoff is an uncalibrated heuristic; see Configuration.

## Error codes

| Code | Meaning |
|---|---|
| 400 | Invalid or empty document/question |
| 404 | Document not found |
| 413 | Upload exceeds configured limit |
| 415 | Unsupported extension |
| 422 | Request validation error |
| 502 | Ollama, embedding, indexing, or generation failure |
| 503 | Database unavailable or query failed |
