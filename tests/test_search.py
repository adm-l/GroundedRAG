import uuid

from app import main


class FakeResult:
    def fetchall(self):
        return [(
            uuid.UUID("f73608bf-e749-4645-8925-bb1a0e172b0b"),
            "sample1.txt",
            0,
            "Node.js is scaled using worker threads and cluster module.",
            0.4047,
        )]


class FakeConnection:
    def __init__(self):
        self.query = None
        self.params = None

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, query, params=None):
        self.query = query
        self.params = params
        return FakeResult()


def test_search_applies_distance_cutoff_and_deduplicates_chunks(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(main, "generate_embedding", lambda _question: [0.0] * 768)
    monkeypatch.setattr(main, "get_connection", lambda: connection)
    monkeypatch.setattr(main, "register_vector", lambda _connection: None)

    results = main._search("Which modules scale Node.js?", top_k=3)

    assert len(results) == 1
    assert results[0].filename == "sample1.txt"
    assert results[0].distance == 0.4047
    assert "ROW_NUMBER() OVER" in connection.query
    assert "PARTITION BY content" in connection.query
    assert "WHERE distance <= %s" in connection.query
    assert connection.params[1] == main.MAX_COSINE_DISTANCE
    assert connection.params[2] == 3
