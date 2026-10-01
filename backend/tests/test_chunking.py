from rag.chunking import chunk_text


def test_empty_text_returns_no_chunks():
    assert chunk_text("") == []


def test_text_shorter_than_chunk_size_returns_one_chunk():
    text = "one two three"
    assert chunk_text(text, chunk_size=400, overlap=40) == [text]


def test_chunk_boundaries_and_overlap():
    words = [f"w{i}" for i in range(10)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=4, overlap=1)

    assert chunks == [
        "w0 w1 w2 w3",
        "w3 w4 w5 w6",
        "w6 w7 w8 w9",
    ]


def test_last_chunk_lands_exactly_on_a_boundary_without_duplication():
    words = [f"w{i}" for i in range(8)]
    text = " ".join(words)

    chunks = chunk_text(text, chunk_size=4, overlap=1)

    assert chunks == ["w0 w1 w2 w3", "w3 w4 w5 w6", "w6 w7"]
