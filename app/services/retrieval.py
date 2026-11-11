import math
import re
import sqlite3
from collections import Counter

STOP_WORDS = {"the", "and", "for", "are", "you", "your", "with", "that", "this", "from", "have", "what", "when", "where", "how", "can", "does", "will", "our", "not", "but", "was", "were", "has", "had", "its", "about", "into", "get", "i", "a", "an", "of", "to", "in", "on", "is", "it", "or", "be", "as", "at", "by"}


def tokenize(text: str) -> list[str]:
    return [word for word in re.findall(r"[a-z0-9]+", text.lower()) if word not in STOP_WORDS]


def retrieve(db: sqlite3.Connection, question: str, limit: int = 4) -> list[dict]:
    query_terms = tokenize(question)
    if not query_terms:
        return []
    rows = db.execute("SELECT chunks.text, documents.filename FROM chunks JOIN documents ON documents.id = chunks.document_id").fetchall()
    if not rows:
        return []
    docs = [(row["text"], row["filename"], Counter(tokenize(row["text"]))) for row in rows]
    df = Counter(term for _, _, terms in docs for term in terms.keys())
    scored = []
    for text, filename, terms in docs:
        score = sum((1 + math.log(terms[term])) * (math.log(1 + len(docs) / (1 + df[term]))) for term in set(query_terms) if terms[term])
        if score:
            scored.append((score, text, filename))
    if not scored:
        return []
    top = sorted(scored, reverse=True)[:limit]
    query_vocabulary = set(query_terms)
    results = []
    for _rank_score, text, filename in top:
        matched_terms = query_vocabulary.intersection(tokenize(text))
        coverage = len(matched_terms) / len(query_vocabulary)
        # A simple relevance signal based on query-term coverage, not a probability.
        results.append({"text": text, "filename": filename, "score": round(coverage * 0.9, 4)})
    return results
