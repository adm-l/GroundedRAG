import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from app.config import EMBEDDING_DIMENSIONS, OLLAMA_BASE_URL, OLLAMA_EMBED_MODEL


def generate_embedding(text: str) -> list[float]:
    payload = {"model": OLLAMA_EMBED_MODEL, "input": text}
    request = Request(f"{OLLAMA_BASE_URL.rstrip('/')}/api/embed", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode())
    except HTTPError as exc:
        raise RuntimeError(f"Ollama embedding request failed (HTTP {exc.code})") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("Could not connect to Ollama embedding service") from exc
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError("Ollama returned an invalid embedding response") from exc
    embeddings = result.get("embeddings")
    if not isinstance(embeddings, list) or not embeddings or not isinstance(embeddings[0], list):
        raise RuntimeError("Ollama response did not contain an embedding")
    vector = embeddings[0]
    if len(vector) != EMBEDDING_DIMENSIONS:
        raise RuntimeError(f"Expected {EMBEDDING_DIMENSIONS} dimensions; received {len(vector)}")
    return [float(value) for value in vector]
