# Roadmap

## Next improvements

- [ ] Add integration tests for PostgreSQL and Ollama.
- [ ] Measure distance distributions for relevant and unrelated questions; then calibrate a relevance threshold.
- [ ] Add explicit no-match behavior and retrieval evaluation.
- [ ] Add document deletion and clearer processing state transitions.
- [ ] Add token-aware or structure-aware chunking.
- [ ] Add model latency and retrieval metrics.

## Production hardening

- [ ] Authentication, authorization, and tenant isolation.
- [ ] Rate limiting and per-user quotas.
- [ ] Durable background indexing workers and retries.
- [ ] Versioned schema migrations and tested backups.
- [ ] Structured logs, request IDs, tracing, and alerts.
- [ ] Timeouts, cancellation, graceful shutdown.
- [ ] Evaluation data for retrieval precision, answer faithfulness, and abstention.
- [ ] Prompt-injection and data-exfiltration tests.
- [ ] Dependency pinning and vulnerability scanning.

No GitHub Actions, CI workflow, or workflow files are included, as requested.
