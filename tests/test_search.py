import uuid

from app import main


def _row(document_id, filename, content, distance, chunk_index=0):
    return (uuid.UUID(document_id), filename, chunk_index, content, distance)


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self, rows):
        self.query = None
        self.params = None
        self.rows = rows

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.query = query
        self.params = params
        return FakeResult(self.rows)


def _patch_search_dependencies(monkeypatch, connection):
    monkeypatch.setattr(main, "generate_embedding", lambda _question: [0.0] * 768)
    monkeypatch.setattr(main, "get_connection", lambda: connection)
    monkeypatch.setattr(main, "register_vector", lambda _connection: None)


def test_search_deduplicates_whitespace_variants_and_keeps_closest(monkeypatch):
    connection = FakeConnection([
        _row(
            "f73608bf-e749-4645-8925-bb1a0e172b0b",
            "sample1.txt",
            "Node.js is scaled using worker threads and cluster module.",
            0.4047,
        ),
        _row(
            "5207d2dd-182b-462e-bf9c-1d4259a5eae8",
            "sample1.txt",
            "  Node.js   is scaled using worker threads and cluster module.\n",
            0.4082,
        ),
        _row(
            "0ce23e83-4555-43ab-9a27-aabce80fcb72",
            "sample.txt",
            "Redis provides caching and rate limiting.",
            0.42,
        ),
    ])
    _patch_search_dependencies(monkeypatch, connection)

    results = main._search("Which modules scale Node.js?", top_k=3)

    assert len(results) == 2
    assert results[0].document_id == uuid.UUID("f73608bf-e749-4645-8925-bb1a0e172b0b")
    assert results[0].distance == 0.4047
    assert results[1].content == "Redis provides caching and rate limiting."
    assert "ROW_NUMBER() OVER" in connection.query
    assert "PARTITION BY btrim(regexp_replace(content" in connection.query
    assert "WHERE distance <= %s" in connection.query
    assert connection.params[1] == main.MAX_COSINE_DISTANCE
    assert connection.params[2] == 3


def test_search_python_guard_removes_duplicate_rows_from_database(monkeypatch):
    duplicate_content = "Worker Threads and Cluster module scale Node.js."
    connection = FakeConnection([
        _row(
            "f73608bf-e749-4645-8925-bb1a0e172b0b",
            "sample1.txt",
            duplicate_content,
            0.30,
        ),
        _row(
            "5207d2dd-182b-462e-bf9c-1d4259a5eae8",
            "sample1.txt",
            duplicate_content,
            0.31,
        ),
    ])
    _patch_search_dependencies(monkeypatch, connection)

    results = main._search("Which modules scale Node.js?", top_k=3)

    assert len(results) == 1
    assert results[0].distance == 0.30
