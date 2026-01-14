"""User and RBAC models."""
from enum import Enum
from typing import Optional, List, TYPE_CHECKING
from sqlmodel import Field, Relationship, SQLModel
from .base import TimestampMixin

if TYPE_CHECKING:
    from .tenant import Organization
    from .installation import InstallationSession



class UserRoleEnum(str, Enum):
    """User role enumeration for RBAC."""
    SUPER_ADMIN = "super_admin"           # Full system access
    PLATFORM_MANAGER = "platform_manager" # Manage installers globally
    ORG_MANAGER = "org_manager"           # Manage organization
    ORG_VIEWER = "org_viewer"             # Read-only org access
    INSTALLER = "installer"                # Install and validate meters


class UserBase(SQLModel):
    """Base user attributes."""
    username: str = Field(index=True, unique=True)
    email: str = Field(index=True, unique=True)
    full_name: Optional[str] = None
    is_active: bool = Field(default=True)


class User(UserBase, TimestampMixin, table=True):
    """
    Enhanced User model with RBAC support.
    
    Users can have:
    - A platform-level role (super_admin, platform_manager)
    - Organization-specific roles via UserOrganizationRole junction table
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str
    
    # Platform-level role (nullable for org-only users)
    platform_role: Optional[str] = Field(default=None)  # UserRoleEnum value
    
    # Relationships
    organization_roles: List["UserOrganizationRole"] = Relationship(back_populates="user")
    installations: List["InstallationSession"] = Relationship(back_populates="installer")


class UserOrganizationRoleBase(SQLModel):
    """Base attributes for user-organization-role junction."""
    user_id: int = Field(foreign_key="user.id")
    organization_id: int = Field(foreign_key="organization.id")
    role: str  # UserRoleEnum value (org_manager, org_viewer, installer)
    is_active: bool = Field(default=True)


class UserOrganizationRole(UserOrganizationRoleBase, TimestampMixin, table=True):
    """
    Junction table for User-Organization-Role mapping.
    
    Allows users to have different roles in different organizations.
    Example: A user can be an installer in Org A and org_manager in Org B.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Relationships
    user: User = Relationship(back_populates="organization_roles")
    organization: "Organization" = Relationship(back_populates="users")
