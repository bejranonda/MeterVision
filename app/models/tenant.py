"""Tenant/Organization models for multi-tenancy."""
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from .base import TimestampMixin, SoftDeleteMixin

if TYPE_CHECKING:
    from .user_rbac import UserOrganizationRole
    from .asset import Project
    from .device import Camera



class OrganizationBase(SQLModel):
    """Base organization attributes."""
    name: str = Field(index=True)
    subdomain: Optional[str] = Field(default=None, index=True, unique=True)
    is_active: bool = Field(default=True)
    billing_status: str = Field(default="trial")  # trial, active, suspended, cancelled


class Organization(OrganizationBase, TimestampMixin, SoftDeleteMixin, table=True):
    """
    Organization (Tenant) entity.
    
    Represents a customer organization using the meter reading service.
    All data is scoped to organizations for multi-tenant isolation.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    settings: Optional["OrganizationSettings"] = Relationship(back_populates="organization")
    users: List["UserOrganizationRole"] = Relationship(back_populates="organization")
    projects: List["Project"] = Relationship(back_populates="organization")
    cameras: List["Camera"] = Relationship(back_populates="organization")


class OrganizationRead(OrganizationBase, TimestampMixin):
    """Organization response model without relationships."""
    id: int


class OrganizationSettingsBase(SQLModel):
    """Base settings attributes."""
    organization_id: int = Field(foreign_key="organization.id")
    settings_json: str = Field(default="{}")  # JSON string for flexible settings
    
    
class OrganizationSettings(OrganizationSettingsBase, TimestampMixin, table=True):
    """
    Organization-specific configuration settings.
    
    Stores flexible settings as JSON (e.g., branding, features, notifications).
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    organization: Organization = Relationship(back_populates="settings")
