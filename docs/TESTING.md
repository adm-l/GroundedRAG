# Testing

## Automated unit tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pytest -q
```

The unit suite covers chunking boundaries and invalid settings, the LLM prompt contract and empty model responses, and the retrieval query's similarity cutoff and duplicate-chunk filtering. Ollama and PostgreSQL are mocked in these unit tests.

## Local integration smoke tests

Start Ollama and the Docker Compose stack. Then check the API and database readiness:

```bash
curl -sS http://localhost:8000/health/live
curl -sS http://localhost:8000/health/ready
```

Upload a document:

```bash
curl -sS -X POST http://localhost:8000/documents \
  -F 'file=@sample1.txt;type=text/plain'
```

Copy the returned id (UUID), then index it:

```bash
curl -sS -X POST 'http://localhost:8000/documents/REPLACE_WITH_DOCUMENT_UUID/process'
```

Search for relevant chunks:

```bash
curl -sS -X POST http://localhost:8000/search \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which modules are used to scale Node.js?","top_k":3}'
```

Ask a question and receive an answer with source chunks:

```bash
curl -sS -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which modules are used to scale Node.js?","top_k":3}'
```

Try an unanswerable question (for example, “Who is the CEO of the company?”) when that fact is absent from your uploaded files. It should abstain rather than invent an answer. This is a manual smoke test, not a deterministic assertion about local LLM output.

Upload the exact same file again. The API should return HTTP 200 and the existing document id. Duplicate chunks are filtered during search after whitespace normalization; the closest matching chunk is retained. Unit tests cover both normalized duplicates and a Python-side fallback guard. The default maximum cosine distance is 0.45; tune MAX_COSINE_DISTANCE against a representative evaluation set before relying on it.

## Recommended additional coverage

- Upload validation and duplicate-upload race conditions (application-level deduplication is not a database uniqueness guarantee).
- Missing IDs and status transitions.
- Ollama timeout, HTTP errors, malformed responses, and wrong embedding dimensions.
- Database failures in each endpoint.
- Re-indexing and transaction rollback.
- Retrieval relevance and answer faithfulness using a labeled evaluation set.
- Prompt injection inside uploaded documents.

Database/Ollama integration tests should remain separate from the fast unit-test suite.
