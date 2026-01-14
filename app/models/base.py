"""Base models and mixins for the application."""
from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel


class TimestampMixin(SQLModel):
    """Mixin to add created_at and updated_at timestamps to models."""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class SoftDeleteMixin(SQLModel):
    """Mixin to add soft delete functionality to models."""
    is_deleted: bool = Field(default=False)
    deleted_at: Optional[datetime] = None
