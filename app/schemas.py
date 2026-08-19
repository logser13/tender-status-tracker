from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.status import TenderStatus


class TenderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    customer: Optional[str] = Field(default=None, max_length=255)


class TenderUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    customer: Optional[str] = Field(default=None, max_length=255)


class TenderRead(BaseModel):
    id: int
    title: str
    description: Optional[str]
    customer: Optional[str]
    status: TenderStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class StatusUpdateRequest(BaseModel):
    new_status: TenderStatus
    changed_by: str = Field(min_length=1, max_length=255)
    reason: str = Field(min_length=1, max_length=1000)


class StatusTransitionResponse(BaseModel):
    id: int
    tender: TenderRead
    history: "HistoryEntry"


class HistoryEntry(BaseModel):
    id: int
    tender_id: int
    old_status: Optional[TenderStatus]
    new_status: TenderStatus
    changed_by: str
    reason: str
    changed_at: datetime

    model_config = ConfigDict(from_attributes=True)


HistoryEntry.model_rebuild()
