"""RBAC middleware and permission checking utilities."""
from typing import List, Optional
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select
from functools import wraps

from ..models import User, UserRoleEnum, UserOrganizationRole, Organization
from ..database import get_session
from ..auth import get_current_user


class PermissionChecker:
    """
    Dependency class for checking user permissions.
    
    Usage:
        @app.get("/protected")
        def protected_route(
            permission: PermissionChecker = Depends(PermissionChecker(require_role=[UserRoleEnum.ORG_MANAGER]))
        ):
            pass
    """
    
    def __init__(
        self,
        require_role: Optional[List[UserRoleEnum]] = None,
        require_org_access: bool = False
    ):
        self.require_role = require_role or []
        self.require_org_access = require_org_access
    
    def __call__(
        self,
        current_user: User = Depends(get_current_user),
        session: Session = Depends(get_session)
    ) -> User:
        """Check if current user has required permissions."""
        
        # Super admin bypasses all checks
        if current_user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
            return current_user
        
        # Check if user has required role (platform or org-level)
        if self.require_role:
            has_permission = False
            
            # Check platform role
            if current_user.platform_role in [role.value for role in self.require_role]:
                has_permission = True
            
            # Check org roles
            if not has_permission:
                user_org_roles = session.exec(
                    select(UserOrganizationRole)
                    .where(UserOrganizationRole.user_id == current_user.id)
                    .where(UserOrganizationRole.is_active == True)
                ).all()
                
                for org_role in user_org_roles:
                    if org_role.role in [role.value for role in self.require_role]:
                        has_permission = True
                        break
            
            if not has_permission:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"User does not have required role: {[r.value for r in self.require_role]}"
                )
        
        return current_user


async def get_current_user_org_context(
    organization_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
) -> tuple[User, Organization]:
    """
    Verify user has access to the specified organization and return both user and org.
    
    Args:
        organization_id: The organization ID being accessed
        current_user: The authenticated user
        session: Database session
    
    Returns:
        Tuple of (User, Organization)
    
    Raises:
        HTTPException: If user doesn't have access to the organization
    """
    # Super admin can access any organization
    if current_user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
        org = session.exec(select(Organization).where(Organization.id == organization_id)).first()
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        return current_user, org
    
    # Check if user has any role in this organization
    user_org_role = session.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.user_id == current_user.id)
        .where(UserOrganizationRole.organization_id == organization_id)
        .where(UserOrganizationRole.is_active == True)
    ).first()
    
    if not user_org_role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User does not have access to this organization"
        )
    
    org = session.exec(select(Organization).where(Organization.id == organization_id)).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    return current_user, org


def check_org_access(user_id: int, organization_id: int, session: Session) -> bool:
    """
    Check if user has access to an organization.
    
    Args:
        user_id: The user ID to check
        organization_id: The organization ID
        session: Database session
    
    Returns:
        True if user has access, False otherwise
    """
    # Get user
    user = session.get(User, user_id)
    if not user:
        return False
    
    # Super admin has access to everything
    if user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
        return True
    
    # Check org membership
    user_org_role = session.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.user_id == user_id)
        .where(UserOrganizationRole.organization_id == organization_id)
        .where(UserOrganizationRole.is_active == True)
    ).first()
    
    return user_org_role is not None


# Convenience dependencies for common permission checks

def require_super_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require Super Admin role."""
    if current_user.platform_role != UserRoleEnum.SUPER_ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super Admin access required"
        )
    return current_user


def require_platform_manager(
    current_user: User = Depends(get_current_user)
) -> User:
    """Require Platform Manager or Super Admin role."""
    if current_user.platform_role not in [
        UserRoleEnum.SUPER_ADMIN.value,
        UserRoleEnum.PLATFORM_MANAGER.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform Manager access required"
        )
    return current_user
