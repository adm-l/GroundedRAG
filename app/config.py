import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://rag:rag_dev_password@localhost:5433/ragdb")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_EMBED_MODEL = os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
OLLAMA_CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "qwen3:4b")
EMBEDDING_DIMENSIONS = int(os.getenv("EMBEDDING_DIMENSIONS", "768"))
MAX_DOCUMENT_BYTES = int(os.getenv("MAX_DOCUMENT_BYTES", str(2 * 1024 * 1024)))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

# Initial heuristic, not a calibrated probability. Tune against a labeled query set.
MAX_COSINE_DISTANCE = float(os.getenv("MAX_COSINE_DISTANCE", "0.70"))
if not 0.0 <= MAX_COSINE_DISTANCE <= 2.0:
    raise ValueError("MAX_COSINE_DISTANCE must be between 0.0 and 2.0")
