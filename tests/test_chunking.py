import pytest
from app.chunking import split_text


def test_empty_text_returns_no_chunks():
    assert split_text("   ") == []


def test_short_text_is_one_chunk():
    assert split_text("hello world", chunk_size=20, overlap=2) == ["hello world"]


def test_long_text_is_split_with_overlap():
    chunks = split_text("abcdefghij" * 5, chunk_size=20, overlap=5)
    assert len(chunks) > 1
    assert all(chunks)
    assert all(len(chunk) <= 20 for chunk in chunks)


@pytest.mark.parametrize("chunk_size,overlap", [(0, 0), (10, -1), (10, 10), (10, 11)])
def test_invalid_chunk_configuration_raises(chunk_size, overlap):
    with pytest.raises(ValueError):
        split_text("some text", chunk_size, overlap)
