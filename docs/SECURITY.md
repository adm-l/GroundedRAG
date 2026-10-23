# Security

## Implemented

- Only .txt and .md filename extensions are accepted.
- Upload byte limit, UTF-8 decoding, and non-empty content are validated.
- SQL uses parameters rather than string concatenation.
- Pydantic limits question length and top_k.
- Uploaded content is never executed.
- The answer prompt treats retrieved text as untrusted data.

## Gaps before public deployment

There is no authentication, authorization, tenant isolation, rate limiting, quotas, content scanning, durable job queue, or complete request timeout budget. Prompt injection defenses are not guaranteed by system instructions. The sample database password is for local development only. The API has no audit/retention policy or document deletion endpoint.

Keep the service private until access control is implemented. Use TLS, secrets management, least-privilege database credentials, schema migrations, structured redaction-safe logs, metrics, and adversarial tests. Evaluate answers against a curated dataset rather than treating generated text as verified fact.
