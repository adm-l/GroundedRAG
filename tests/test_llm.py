import json

from app import llm


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def test_generate_answer_sends_grounding_and_semantic_matching_instructions(monkeypatch):
    captured = {}

    def fake_urlopen(request, timeout):
        captured["request"] = request
        captured["timeout"] = timeout
        return FakeResponse({"message": {"content": "Worker Threads and Cluster."}})

    monkeypatch.setattr(llm, "urlopen", fake_urlopen)

    answer = llm.generate_answer(
        "Which modules scale Node.js?",
        "Source: notes.txt\nNode.js is scaled using worker threads and cluster module.",
    )

    payload = json.loads(captured["request"].data.decode())
    system_prompt = payload["messages"][0]["content"]
    user_prompt = payload["messages"][1]["content"]

    assert answer == "Worker Threads and Cluster."
    assert captured["timeout"] == 120
    assert "do not require the question to use the exact same words" in system_prompt
    assert "context genuinely does not contain enough information" in system_prompt
    assert "Do not invent facts" in system_prompt
    assert "Node.js is scaled using worker threads and cluster module." in user_prompt
    assert payload["options"]["temperature"] == 0


def test_generate_answer_rejects_empty_model_response(monkeypatch):
    monkeypatch.setattr(llm, "urlopen", lambda *_args, **_kwargs: FakeResponse({"message": {"content": "  "}}))

    try:
        llm.generate_answer("question", "context")
    except RuntimeError as exc:
        assert "empty answer" in str(exc)
    else:
        raise AssertionError("Expected empty model response to raise RuntimeError")
