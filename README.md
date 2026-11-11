# SupportIQ

SupportIQ is a small, runnable customer-support knowledge retrieval app. Upload support documents, ask questions, review source passages, and see when the system recommends human follow-up.

## What it does

- Ingests UTF-8 `.txt` and `.md` documents (up to 2 MB each), splits them into overlapping passages, and stores them in SQLite.
- Retrieves passages with a simple local BM25-style lexical ranker.
- Answers in **local demo mode** without credentials by quoting the best matching passage; answers are grounded in retrieved text and include source labels.
- Optionally uses OpenAI to draft a concise answer from the retrieved passages. The app still returns citations from the retrieval step.
- Saves conversation messages and provides a conversation-history endpoint.
- Flags questions with low retrieval confidence for human follow-up.

This is an educational MVP, not a production support service. The local retrieval score reflects query-term coverage and is not a calibrated probability. The OpenAI provider sends the user's question and retrieved passages to the configured API provider.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\\Scripts\\activate
pip install -e '.[dev]'
cp .env.example .env            # Windows: copy .env.example .env
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000>. The included demo knowledge is in `data/sample_faq.md`; upload it using **Choose files** in the UI. API docs are at <http://127.0.0.1:8000/docs>.

### Optional OpenAI answers

Set `OPENAI_API_KEY` in `.env` to enable generated answers. `OPENAI_MODEL` defaults to `gpt-4o-mini`. No key is needed for local demo mode. Keep `.env` private; it is ignored by Git.

### Run tests

```bash
pytest
```

## API overview

- `GET /api/health` — service and answer mode
- `GET /api/documents` — indexed documents
- `POST /api/documents` — upload a `.txt` or `.md` file as multipart field `file`
- `DELETE /api/documents/{id}` — remove a document
- `POST /api/chat` — `{ "question": "...", "conversation_id": null }`
- `GET /api/conversations/{conversation_id}` — saved message history

## Project structure

```text
app/
  main.py                 FastAPI routes and startup
  config.py               Environment-backed settings
  database.py             SQLite schema and connections
  schemas.py              Request and response models
  services/
    ingestion.py          Text cleanup, chunking, document storage
    retrieval.py          Local lexical retrieval
    answering.py          Demo and optional OpenAI answer providers
    chat.py               Conversation persistence and escalation
  static/index.html       Small responsive browser UI
 tests/                   Service and API tests
 data/sample_faq.md       Example support knowledge to upload
```

## Future contribution tasks

1. Add PDF and DOCX ingestion with clear extraction errors.
2. Add semantic embeddings and compare retrieval quality with the lexical baseline.
3. Calibrate confidence using a labeled evaluation set; expose threshold settings in the UI.
4. Add conversation list, rename, and delete controls in the UI.
5. Add authentication, per-workspace document isolation, and audit logs.
6. Add background ingestion, document versioning, and duplicate-content handling.
7. Add answer-quality evaluation, prompt-injection defenses for uploaded content, and observability.
8. Add deployment configuration and CI once a repository is selected.

## Important behavior

The app intentionally supports `.txt` and `.md` only in this MVP. If retrieval finds no matching content, SupportIQ says it cannot answer from the available documents and escalates. In demo mode it returns the top passage rather than inventing a paraphrase. Do not upload private customer data to the demo app.
