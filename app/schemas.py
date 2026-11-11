from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    conversation_id: str | None = None


class Source(BaseModel):
    filename: str
    excerpt: str
    score: float


class ChatResponse(BaseModel):
    conversation_id: str
    answer: str
    confidence: float
    escalated: bool
    escalation_reason: str | None = None
    sources: list[Source]


class DocumentResponse(BaseModel):
    id: int
    filename: str
    created_at: str
