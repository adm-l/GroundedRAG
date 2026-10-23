# Testing

## Automated unit tests

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
```

Current tests cover text chunking, empty input, overlap, and invalid configuration.

## Integration smoke tests

Start PostgreSQL and Ollama, start the API, then follow the upload/index/search/ask steps in INSTALLATION.md.

## Recommended additional coverage

- Upload success, invalid extension, invalid UTF-8, empty files, and size limits.
- Missing IDs and status transitions.
- Ollama timeout, HTTP errors, malformed responses, and wrong embedding dimensions.
- Database failures in each endpoint.
- Re-indexing and transaction rollback.
- Empty index and unrelated questions.
- Prompt injection inside uploaded documents.
- Retrieval relevance and answer faithfulness using labeled examples.

Database/Ollama tests should be separate integration tests, not part of the fast unit-test suite.
