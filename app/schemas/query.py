from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class QueryRequest(BaseModel):
    question: str
    document_id: Optional[UUID] = None


class Citation(BaseModel):
    document_id: UUID
    filename: str
    chunk_index: int
    excerpt: str

    model_config = ConfigDict(from_attributes=True)


class QueryResponse(BaseModel):
    answer: str
    citations: List[Citation] = []
    is_fallback: bool = False


class QAHistoryEntry(BaseModel):
    id: UUID
    question: str
    answer: str
    citations: List[Citation] = []
    is_fallback: bool = False
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
