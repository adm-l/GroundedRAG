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

Start Ollama and the Docker Compose stack. The default API base URL is `http://localhost:8000`. If you changed the host port mapping because port 8000 is already occupied, replace the URL below with your mapped port (for example, `http://localhost:8001`). The API container still listens on port 8000 internally.

Check the API and database readiness:

```bash
curl -sS http://localhost:8000/health/live
curl -sS http://localhost:8000/health/ready
```

Upload a document:

```bash
curl -sS -X POST http://localhost:8000/documents \
  -F 'file=@sample1.txt;type=text/plain'
```

Copy the returned `id` (UUID), then index it:

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

For the sample document containing the sentence about Node.js scaling, the answer should mention `worker threads` and the `cluster` module and include the relevant source chunk. Verify that the answer is supported by the returned source; a low cosine distance is not a calibrated confidence score.

Try an unanswerable question when the fact is absent from all uploaded files:

```bash
curl -sS -X POST http://localhost:8000/ask \
  -H 'Content-Type: application/json' \
  -d '{"question":"Which cloud provider does our backend use?","top_k":3}'
```

The expected behavior is to state that the documents do not provide the information, rather than invent a provider. This is a manual smoke test, not a deterministic assertion about local LLM output; inspect both the answer and its sources.

## Duplicate retrieval test

Uploading the exact same bytes twice tests document-level deduplication: the second upload should return HTTP 200 and the existing document ID. It does **not** create a second document record, so it is not by itself a test of duplicate-chunk retrieval.

To test duplicate-chunk filtering across separate document records, create a second text file with the same sentence content but different whitespace (so its SHA-256 differs), upload and index it as a separate document, and run the same `/search` query. The normalized duplicate chunk should appear only once, with the closest matching chunk retained. The automated tests cover normalized duplicates and a Python-side fallback guard.

The default maximum cosine distance is 0.45; tune `MAX_COSINE_DISTANCE` against a representative evaluation set before relying on it.

## Recommended additional coverage

- Upload validation and duplicate-upload race conditions (application-level deduplication is not a database uniqueness guarantee).
- Missing IDs and status transitions.
- Ollama timeout, HTTP errors, malformed responses, and wrong embedding dimensions.
- Database failures in each endpoint.
- Re-indexing and transaction rollback.
- Retrieval relevance and answer faithfulness using a labeled evaluation set.
- Prompt injection inside uploaded documents.

Database/Ollama integration tests should remain separate from the fast unit-test suite.
