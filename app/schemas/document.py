from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    id: UUID
    filename: str
    owner_id: UUID
    status: str  # "processing" | "ready" | "failed"
    uploaded_at: datetime
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DocumentStatus(BaseModel):
    id: UUID
    filename: str
    status: str
    error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
