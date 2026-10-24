# LLM, RAG, and Agent Parameters: Practical Guide

This guide explains the configuration values and request parameters commonly encountered when building LLM applications, Retrieval-Augmented Generation (RAG) systems, and AI agents. It distinguishes parameters used by **this GroundedRAG project** from parameters that are **common in other frameworks or future agent implementations**.

The names and availability of model-generation options vary by provider and model. Do not assume that every parameter listed here is supported by Ollama, every model, or this repository.

## 1. Start with the three layers

- **LLM (large language model):** generates text from a prompt. Generation parameters influence style, randomness, length, and stopping.
- **RAG:** retrieves relevant document passages and supplies them as evidence to the LLM. RAG parameters influence chunking, embeddings, retrieval quality, context size, and grounding.
- **Agent:** chooses and executes actions/tools in a loop. Agent parameters influence tool selection, iteration limits, permissions, timeouts, and recovery.

These layers interact, but their settings solve different problems. Increasing an LLM token limit will not fix a retrieval query that returns no chunks. Increasing a retrieval threshold will not make a model's reasoning more reliable by itself.

## 2. Parameters used by GroundedRAG

The project uses FastAPI, Ollama, PostgreSQL, and pgvector. Defaults below reflect the repository configuration; environment variables in your local Docker Compose file can override them.

| Parameter | Current project default | Purpose | If increased/changed | Practical guidance |
|---|---|---|---|---|
| `DATABASE_URL` | Compose constructs URL for PostgreSQL service | Tells the API how to connect to the database | Wrong host/credentials/database cause connection failures; a remote database changes latency and security exposure | In Compose, use the service hostname `db`, not `localhost`. Keep credentials out of Git |
| `POSTGRES_DB` | `ragdb` | Database created by Compose | Different name changes the target database; existing volumes may retain previously initialized settings | Match the database URL; changing this does not automatically rename an existing database |
| `POSTGRES_USER` | `rag` | Database role | Changes connection identity and permissions | Use least privilege outside local development |
| `POSTGRES_PASSWORD` | Development placeholder | Database password | Weak/reused credentials increase compromise risk | Replace for shared environments; never commit a real secret |
| `POSTGRES_HOST_PORT` | `5433` in repository Compose | Host port mapped to PostgreSQL's container port 5432 | A different host port affects host-side clients, not the internal API-to-DB port | Compose API connects to `db:5432`; the Mac connects through the mapped port |
| `OLLAMA_BASE_URL` | Host Ollama URL in Compose | Address of the Ollama API | Wrong/unreachable URL causes embedding or generation timeouts/failures | Test connectivity from the API container, not only from the host |
| `OLLAMA_EMBED_MODEL` | `nomic-embed-text` | Model that turns text into vectors | Different models produce different vector spaces and quality/latency profiles | Re-embed all stored chunks when changing embedding models; don't compare vectors from incompatible models |
| `OLLAMA_CHAT_MODEL` | `qwen3:4b` | Model that writes the final answer | Larger models may improve quality but consume more RAM and respond more slowly | On an 8 GB Mac, monitor memory and latency |
| `EMBEDDING_DIMENSIONS` | `768` | Validates expected embedding length | Mismatch can cause validation or database errors | The schema uses `vector(768)`; changing this variable alone does not migrate the schema |
| `CHUNK_SIZE` | `1000` characters | Maximum text chunk size in the current implementation | Larger chunks preserve more context but can dilute retrieval and use more context tokens; smaller chunks can lose context and create more rows | Tune using real documents and retrieval tests; this setting is characters in this project, not necessarily tokens |
| `CHUNK_OVERLAP` | `150` characters | Repeats boundary text between adjacent chunks | More overlap preserves context at boundaries but increases duplicated text, storage, embedding calls, and duplicate retrieval | Keep smaller than chunk size; tune with chunk size together |
| `MAX_DOCUMENT_BYTES` | `2097152` (2 MiB) | Maximum uploaded document size | Higher limits increase request memory, processing time, and abuse potential | Use a limit consistent with API and infrastructure limits |
| `MAX_COSINE_DISTANCE` | `0.45` in repository defaults | Maximum cosine distance accepted by retrieval | Higher values admit more distant candidates, increasing recall and false positives; lower values reduce noise but may return no results | This is a distance cutoff, not a probability. Calibrate on representative questions. A local value of `0.70` was used while diagnosing an empty result set |
| `top_k` | `3` for search/ask request; API validates its allowed range | Maximum number of chunks returned by retrieval | Higher values provide more evidence but add noise, prompt tokens, latency, and cost/compute | Start small (e.g. 3–5) and evaluate answer quality; use only the range enforced by the endpoint |

**Important:** the exact effective value is the one loaded by the running API process. A local Python file change does not necessarily update an existing Docker image/container. Compose environment variables override defaults in code; recreate the container after changing its environment.

## 3. Common LLM generation parameters

These are common concepts, not a promise that every one is exposed by the current GroundedRAG endpoint. Exact option names and ranges depend on the model/API.

| Parameter | Meaning | Higher/lower side effects | Tuning advice |
|---|---|---|---|
| Temperature | Controls randomness in token selection | Higher: more varied and less predictable. Lower: more repeatable and conservative | For grounded QA, start low (often 0–0.3); low temperature does not guarantee factual correctness |
| Top-p | Nucleus sampling: limits selection to tokens within a cumulative probability mass | Lower: narrower/more conservative choices; higher: more diversity | Usually tune temperature OR top-p first, not both at once |
| Top-k | Limits candidates to the k most likely tokens (provider-dependent) | Lower: fewer choices; higher: more options and variation | Not the same as RAG `top_k`, which selects document chunks |
| Max output tokens / `num_predict` | Maximum generated tokens | Higher: longer possible answers but more latency and memory; lower: answers may truncate | Set to the longest useful response, not an unlimited value |
| Stop sequences | Strings/tokens that stop generation | Too broad can cut off a valid answer; too narrow may not stop unwanted continuation | Add only when the output format requires it |
| Seed | Requests repeatable sampling when supported | Can improve reproducibility, but deterministic behavior is not guaranteed across hardware/model versions | Use for experiments, not as a correctness control |
| Context window / `num_ctx` | Maximum tokens the model can process in a context | Higher: can fit more evidence but increases memory and may reduce throughput | Must fit system prompt + question + retrieved chunks + output budget; hardware/model limits apply |
| Repeat penalty | Discourages repeated tokens/phrases | Too high can make wording unnatural or suppress necessary terms; too low may allow loops | Use only if repetition is observed |
| Presence penalty | Encourages introducing tokens/topics not yet used (where supported) | High values can push the answer away from evidence | Usually keep low for factual RAG |
| Frequency penalty | Penalizes tokens in proportion to prior use (where supported) | High values can distort technical answers with repeated identifiers or terms | Often unnecessary for grounded technical QA |
| Request timeout | Maximum wait for the model call | Too low causes false timeouts; too high ties up workers during hangs | Choose from measured latency and enforce an overall request deadline |
| Streaming | Sends generated tokens progressively | Improves perceived latency but complicates cancellation, partial failures, and clients | Add only when the API/client needs it |
| Structured output / JSON schema | Constrains output shape when supported | Strict schemas improve parsing but can fail if schema is too complex or unsupported | Validate output server-side; never trust model output as inherently valid |

### Ollama-specific notes

Ollama commonly exposes options such as `temperature`, `top_p`, `top_k`, `num_predict`, `num_ctx`, `repeat_penalty`, and `seed` through its API or model configuration. Support and behavior can vary by model/version. The current project may not expose all of them as application settings. Do not add an option to a config file unless the code passes it to Ollama.

## 4. RAG ingestion and embedding parameters

| Parameter/concept | Purpose | Side effects / trade-offs | How to tune |
|---|---|---|---|
| Chunk size | Controls how much source text is embedded and retrieved as one unit | Large chunks may mix topics; small chunks may lose important context | Compare retrieval results across several sizes using the same evaluation questions |
| Chunk overlap | Preserves text around chunk boundaries | Increases storage and duplicate content | Use enough overlap for boundary continuity, but avoid excessive overlap |
| Embedding model | Maps text to a vector representation | Changing it changes the vector space and may alter semantic matching | Re-index all documents after switching model |
| Embedding dimensions | Number of values in each vector | Must match model output and vector column type | Check actual model output and database schema together |
| Text normalization | Handles whitespace/case and other text cleanup | Aggressive cleanup may remove meaningful code, formatting, or identifiers | Normalize whitespace carefully; preserve source text for citations |
| Metadata filters | Restrict retrieval by document, tenant, type, date, or permissions | Incorrect filters can hide relevant evidence or leak cross-tenant data if authorization is wrong | Apply access-control filters on the server, not based on model instructions |
| Similarity metric | Measures vector closeness (cosine distance, inner product, or L2 distance) | Metric and index operator must match; scores aren't interchangeable | This project uses pgvector cosine distance; don't reuse thresholds from a different metric |
| Distance threshold | Rejects candidates beyond a distance cutoff | Strict threshold: empty results; loose threshold: irrelevant context | Measure recall and false positives on known questions |
| Retrieval `top_k` | Number of candidate chunks passed onward | Too low misses evidence; too high adds noise and prompt size | Tune separately from LLM generation parameters |
| Reranking | Reorders candidates using a reranker model or scoring method | Better ordering can add latency and compute | Consider only after measuring baseline retrieval quality |
| Hybrid search | Combines keyword and vector search | Helps exact terms/IDs but requires score/rank fusion and more complexity | Useful when docs contain identifiers, error codes, or exact technical terms |
| Query rewriting | Converts a user's question into a search-friendly query | May improve recall but can change intent or add latency | Preserve original question and evaluate rewritten queries |
| Context assembly | Selects and formats retrieved passages for the LLM | Too much context may be truncated or distract the model; too little omits evidence | Include source identifiers and clear delimiters; enforce a context token budget |
| Citation/source return | Associates answers with retrieved document chunks | Incorrect source mapping creates false trust | Return actual retrieved sources and verify that claims are supported |

### Cosine distance: the key distinction

For cosine distance, **smaller generally means closer**. A threshold such as 0.70 means “allow candidates whose distance is at most 0.70”; it does not mean “70% relevant.” The best cutoff depends on the embedding model, corpus, query type, and metric. Tune using both answerable and unanswerable questions.

## 5. Prompt parameters and prompt design

| Item | Purpose | Risk if poorly configured |
|---|---|---|
| System prompt | Sets the assistant's role, constraints, and response behavior | Conflicting instructions cause inconsistent output; a prompt alone is not a security boundary |
| User prompt | Contains the user's actual request | Ambiguity leads to weak retrieval or answers |
| Retrieved context | Supplies evidence from documents | Irrelevant or malicious document text can distract the model or attempt prompt injection |
| Context delimiters | Mark where retrieved evidence starts/ends | Poor separation makes it harder to distinguish instructions from untrusted source text |
| Grounding rule | Tells the model to answer only from provided evidence and admit when evidence is missing | It reduces unsupported answers but does not eliminate hallucinations |
| Answer format | Defines expected sections, JSON, citations, or concise output | Overly rigid formatting may truncate or omit important details |
| Fallback/no-answer message | Defines behavior when retrieval yields no usable evidence | Without a fallback, the model may guess |

Treat retrieved documents as **untrusted data**, not as instructions. Validate permissions and outputs in application code.

## 6. Agent parameters (general design guide)

The current GroundedRAG service is a RAG API, **not yet a general-purpose autonomous agent**. These parameters are relevant if you add tool-using agents later.

| Parameter | Purpose | If too permissive/high | Safer starting practice |
|---|---|---|---|
| Max iterations / max steps | Caps the reasoning-tool loop | Excessive tool calls, latency, and cost; loops | Set a small hard limit and return a clear partial/failure result |
| Max tool calls | Caps total tool invocations | Repeated or unnecessary calls | Enforce independently of model instructions |
| Tool allowlist | Defines tools the agent may invoke | More tools increase attack surface and unintended actions | Expose only necessary tools |
| Tool permissions | Controls read/write/destructive capabilities | Unrestricted access can modify or leak data | Default to read-only; require explicit approval for consequential writes |
| Tool timeout | Maximum duration per tool call | Too low causes false failures; too high ties up workers | Set per-tool and overall deadlines |
| Retry count | Number of retries for transient errors | High retries amplify load and duplicate side effects | Retry only transient errors; use bounded exponential backoff and jitter |
| Max tool output size | Caps returned content | Too low loses evidence; too high consumes context and may leak data | Truncate safely and summarize with provenance |
| Agent context/memory | Preserves prior interaction state | Unbounded history consumes context and can retain sensitive data | Define retention, summarization, and deletion policies |
| Planning mode | Whether to create a plan before acting | Overplanning costs latency; underplanning can miss dependencies | Use planning for multi-step tasks, not simple lookups |
| Human approval | Requires confirmation for high-impact actions | Adds user latency but reduces accidental actions | Require approval for deletes, external messages, payments, permission changes, and production mutations |
| Idempotency key | Prevents repeated side effects for the same logical action | Incorrect key scope can suppress valid operations or permit duplicates | Use for retryable writes and external actions |
| Tool argument schema | Validates arguments before execution | Weak schemas permit malformed or unsafe actions | Validate types, ranges, resource ownership, and allowed values in code |
| Budget/deadline | Caps total time, tokens, or tool cost | Too low can stop valid work; no budget can run away | Enforce a hard total deadline and observable budget |
| Audit log | Records tool name, arguments (redacted), outcome, and actor | Excessive logging may store secrets/PII | Redact secrets and define retention/access controls |

An agent must not be allowed to grant itself permissions. The server is responsible for authorization, validation, rate limits, and approval gates.

## 7. API/runtime and production parameters

| Parameter/concept | Purpose | Side effects / trade-offs |
|---|---|---|
| HTTP timeout | Caps waiting for an upstream call | Too low causes failures; too high consumes connection/worker capacity |
| Connection pool size | Limits concurrent DB connections per process | Too low creates waits; too high can overwhelm PostgreSQL, especially across many replicas |
| Worker/process count | Parallelizes API requests | More workers use more RAM and multiply DB pools; does not automatically make model inference faster |
| Concurrency limit | Caps simultaneous expensive requests | Protects local RAM/LLM but may queue or reject traffic |
| Rate limit | Caps requests per user/IP/tenant | Protects availability; poor key selection can penalize shared IPs or allow bypass |
| Queue size | Buffers background work | Large queues increase memory and wait time; small queues reject work sooner |
| Retry/backoff | Handles transient upstream errors | Unbounded retries create retry storms |
| Cache TTL | Controls how long cached results remain valid | Long TTL can return stale answers; short TTL reduces hit rate |
| Logging level | Controls log detail | Verbose logs can expose sensitive prompts/documents and increase storage |
| Metrics/tracing | Measures latency, errors, token usage, retrieval quality, and tool activity | High-cardinality labels can increase monitoring costs; trace content should be redacted |

## 8. A practical tuning workflow

1. **Record the baseline:** current config, model versions, a fixed set of questions, latency, and results.
2. **Change one variable at a time:** avoid changing chunk size, threshold, and model simultaneously.
3. **Test answerable questions:** verify the expected source chunk is retrieved.
4. **Test unanswerable questions:** verify the API does not invent an answer when evidence is absent.
5. **Measure retrieval separately from generation:** call `/search` first, then `/ask`.
6. **Check resource impact:** record response time, memory, CPU, database connections, and Ollama behavior.
7. **Keep a change log:** value before, value after, test set, outcome, and reason for keeping/reverting.
8. **Change Docker config deliberately:** environment variables override code defaults; recreate the affected service to apply Compose environment changes.
9. **Re-index when required:** changing the embedding model or vector dimensions requires coordinated re-embedding/schema handling, not just a variable edit.
10. **Promote only measured settings:** do not call a value “production-ready” just because one query works.

## 9. Troubleshooting quick reference

| Symptom | First checks |
|---|---|
| Search returns no chunks | Verify documents are indexed, embeddings are non-null, model/dimensions match, actual container threshold, query distance values, and metadata filters |
| Search returns irrelevant chunks | Lower the distance cutoff carefully, reduce noisy chunks, inspect embedding model, evaluate keyword/hybrid search, and build a query test set |
| Correct source retrieved, answer wrong | Inspect assembled context and system prompt, model name, output token limit, and whether the answer is grounded in retrieved text |
| API times out | Separate Ollama embedding, database, and chat-generation latency; check timeouts, concurrency, and model memory |
| Changing config has no effect | Print effective config inside the running container; inspect Compose environment and recreate/rebuild as appropriate |
| Vector dimension error | Compare embedding response length, `EMBEDDING_DIMENSIONS`, and database column type; re-index/migrate consistently |
| Agent repeats tools (future agent) | Enforce hard step/tool budgets, timeouts, bounded retries, and idempotency |

## 10. Safe defaults for this learning project

- Keep secrets in an ignored local `.env`; do not commit credentials or private source documents.
- Keep model generation conservative for factual answers and always evaluate outputs.
- Start with a small retrieval `top_k` and a measured cosine-distance threshold.
- Do not change embedding model without planning a full re-index.
- Keep agent tools read-only by default if agents are added.
- Require approval for destructive or externally consequential actions.
- Add observability and automated tests before increasing concurrency.

## 11. Glossary

- **Parameter:** A value that changes a component's behavior.
- **Default:** Value used when no explicit override is provided.
- **Environment variable:** Runtime configuration passed to a process/container.
- **Embedding:** Numeric vector representing text for similarity comparison.
- **Cosine distance:** A vector distance measure; lower values indicate closer vectors in the typical pgvector cosine-distance setup.
- **Chunk:** A segment of a source document.
- **Top-k:** The maximum number of ranked candidates returned. In RAG, this usually means chunks; in LLM sampling, top-k means token candidates.
- **Recall:** Fraction of relevant items that retrieval successfully finds.
- **Precision:** Fraction of returned items that are relevant.
- **Hallucination:** Content generated without adequate factual support.
- **Grounding:** Connecting an answer to evidence, such as retrieved source passages.
- **Tool call:** An agent's structured request to invoke an external function or service.
- **Idempotency:** Repeating the same logical operation does not create repeated side effects.
