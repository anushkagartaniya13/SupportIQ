import re
import sqlite3


def split_into_chunks(text: str, max_words: int = 180, overlap: int = 30) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks = []
    start = 0
    while start < len(words):
        end = min(start + max_words, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def save_document(db: sqlite3.Connection, filename: str, content: str) -> int:
    content = normalize_text(content)
    if not content:
        raise ValueError("The document is empty.")
    existing = db.execute("SELECT id FROM documents WHERE filename = ?", (filename,)).fetchone()
    if existing:
        document_id = existing["id"]
        db.execute("UPDATE documents SET content = ?, created_at = CURRENT_TIMESTAMP WHERE id = ?", (content, document_id))
        db.execute("DELETE FROM chunks WHERE document_id = ?", (document_id,))
    else:
        cursor = db.execute("INSERT INTO documents(filename, content) VALUES (?, ?)", (filename, content))
        document_id = cursor.lastrowid
    for ordinal, chunk in enumerate(split_into_chunks(content)):
        db.execute("INSERT INTO chunks(document_id, text, ordinal) VALUES (?, ?, ?)", (document_id, chunk, ordinal))
    return document_id
