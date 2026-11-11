import sqlite3
import uuid
from app.config import settings
from app.services.answering import build_answer
from app.services.retrieval import retrieve


def answer_question(db: sqlite3.Connection, question: str, conversation_id: str | None) -> dict:
    conversation_id = conversation_id or str(uuid.uuid4())
    db.execute("INSERT OR IGNORE INTO conversations(id) VALUES (?)", (conversation_id,))
    db.execute("INSERT INTO messages(conversation_id, role, content) VALUES (?, 'user', ?)", (conversation_id, question))
    hits = retrieve(db, question)
    confidence = hits[0]["score"] if hits else 0.0
    escalated = confidence < settings.confidence_threshold
    answer = build_answer(question, hits)
    reason = None
    if escalated:
        reason = "No sufficiently relevant support document was found."
        if "support specialist" not in answer.lower():
            answer += " If you still need help, please contact a support specialist."
    db.execute("INSERT INTO messages(conversation_id, role, content) VALUES (?, 'assistant', ?)", (conversation_id, answer))
    return {
        "conversation_id": conversation_id,
        "answer": answer,
        "confidence": round(confidence, 3),
        "escalated": escalated,
        "escalation_reason": reason,
        "sources": [{"filename": hit["filename"], "excerpt": hit["text"][:400], "score": hit["score"]} for hit in hits],
    }
