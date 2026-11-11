import sqlite3
from app.services.ingestion import save_document, split_into_chunks
from app.services.retrieval import retrieve


def memory_db():
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    db.executescript("CREATE TABLE documents(id INTEGER PRIMARY KEY, filename TEXT, content TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP); CREATE TABLE chunks(id INTEGER PRIMARY KEY, document_id INTEGER, text TEXT, ordinal INTEGER);")
    return db


def test_chunking_overlaps_and_covers_text():
    parts = split_into_chunks(" ".join(f"word{i}" for i in range(20)), max_words=8, overlap=2)
    assert len(parts) == 3
    assert parts[0].split()[-2:] == parts[1].split()[:2]
    assert parts[-1].split()[-1] == "word19"


def test_save_document_and_replace_same_filename():
    db = memory_db()
    doc_id = save_document(db, "guide.md", "  First   password guide. ")
    again = save_document(db, "guide.md", "Refunds arrive in five days.")
    assert doc_id == again
    assert db.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 1
    assert db.execute("SELECT content FROM documents").fetchone()[0] == "Refunds arrive in five days."


def test_retrieval_ranks_matching_document():
    db = memory_db()
    save_document(db, "password.md", "Reset your password from the sign in page using a secure reset link.")
    save_document(db, "shipping.md", "Standard shipping takes three to five business days after dispatch.")
    hits = retrieve(db, "How can I reset my password?", limit=2)
    assert hits
    assert hits[0]["filename"] == "password.md"
