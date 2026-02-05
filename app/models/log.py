from sqlmodel import Field, SQLModel, JSON, Column
from typing import Optional, Dict, Any
from datetime import datetime
from ..models.base import TimestampMixin

class LogBase(SQLModel):
    level: str = Field(index=True)
    message: str
    details: Optional[Dict[str, Any]] = Field(default={}, sa_column=Column(JSON))
    organization_id: Optional[int] = Field(default=None, foreign_key="organization.id")

class Log(LogBase, TimestampMixin, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class LogCreate(LogBase):
    pass

class LogRead(LogBase):
    id: int
    created_at: datetime
