import json
import os
import re
from collections import Counter
from config import CHUNK_SIZE, CHUNK_OVERLAP, MAX_CHUNKS_PER_QUERY

DATA_DIR = "data/knowledge"


def _biz_path(business_id: int) -> str:
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, f"biz_{business_id}.json")


def _load(business_id: int) -> list[dict]:
    path = _biz_path(business_id)
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(business_id: int, chunks: list[dict]):
    with open(_biz_path(business_id), "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _score(query_tokens: list[str], doc_tokens: list[str]) -> float:
    if not doc_tokens:
        return 0.0
    doc_counts = Counter(doc_tokens)
    return sum(doc_counts.get(t, 0) for t in query_tokens) / len(doc_tokens)


def chunk_text(text: str) -> list[str]:
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + CHUNK_SIZE
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start = end - CHUNK_OVERLAP
    return chunks


def add_document(business_id: int, text: str, source: str = "manual") -> int:
    chunks = chunk_text(text)
    if not chunks:
        return 0

    existing = _load(business_id)
    for chunk in chunks:
        existing.append({"text": chunk, "source": source, "tokens": _tokenize(chunk)})
    _save(business_id, existing)
    return len(chunks)


def search(business_id: int, query: str) -> list[str]:
    chunks = _load(business_id)
    if not chunks:
        return []

    query_tokens = _tokenize(query)
    scored = [(c["text"], _score(query_tokens, c.get("tokens", _tokenize(c["text"])))) for c in chunks]
    scored.sort(key=lambda x: x[1], reverse=True)

    return [text for text, score in scored[:MAX_CHUNKS_PER_QUERY] if score > 0]


def clear_knowledge(business_id: int):
    path = _biz_path(business_id)
    if os.path.exists(path):
        os.remove(path)


def get_doc_count(business_id: int) -> int:
    return len(_load(business_id))
