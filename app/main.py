from pathlib import Path
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import get_connection, initialize_database
from app.schemas import ChatRequest, ChatResponse
from app.services.chat import answer_question
from app.services.ingestion import save_document

app = FastAPI(title="SupportIQ", description="Customer-support knowledge retrieval with cited answers and escalation.", version="0.1.0")
STATIC_DIR = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.on_event("startup")
def startup() -> None:
    initialize_database()

@app.get("/", include_in_schema=False)
def home():
    return FileResponse(STATIC_DIR / "index.html")

@app.get("/api/health")
def health():
    return {"status": "ok", "answer_mode": "openai" if settings.openai_api_key else "local-demo"}

@app.get("/api/documents")
def list_documents():
    with get_connection() as db:
        rows = db.execute("SELECT id, filename, created_at FROM documents ORDER BY created_at DESC").fetchall()
        return [dict(row) for row in rows]

@app.post("/api/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    filename = Path(file.filename or "").name
    if not filename or Path(filename).suffix.lower() not in {".txt", ".md"}:
        raise HTTPException(status_code=400, detail="Upload a .txt or .md file.")
    content_bytes = await file.read(settings.max_upload_bytes + 1)
    if len(content_bytes) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the 2 MB upload limit.")
    try:
        content = content_bytes.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="File must use UTF-8 text encoding.") from exc
    try:
        with get_connection() as db:
            document_id = save_document(db, filename, content)
            row = db.execute("SELECT id, filename, created_at FROM documents WHERE id = ?", (document_id,)).fetchone()
            return dict(row)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.delete("/api/documents/{document_id}", status_code=204)
def delete_document(document_id: int):
    with get_connection() as db:
        cursor = db.execute("DELETE FROM documents WHERE id = ?", (document_id,))
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Document not found.")

@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    try:
        with get_connection() as db:
            return answer_question(db, request.question, request.conversation_id)
    except Exception as exc:
        # Avoid returning provider internals, API keys, or database details to the browser.
        raise HTTPException(status_code=502, detail="The answer service is temporarily unavailable.") from exc

@app.get("/api/conversations/{conversation_id}")
def conversation_history(conversation_id: str):
    with get_connection() as db:
        exists = db.execute("SELECT 1 FROM conversations WHERE id = ?", (conversation_id,)).fetchone()
        if not exists:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        rows = db.execute("SELECT role, content, created_at FROM messages WHERE conversation_id = ? ORDER BY id", (conversation_id,)).fetchall()
        return {"conversation_id": conversation_id, "messages": [dict(row) for row in rows]}
