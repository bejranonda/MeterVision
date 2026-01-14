"""Organization management API routes."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from ..database import get_session
from ..models import (
    Organization, OrganizationBase,
    User, UserRoleEnum, UserOrganizationRole, UserOrganizationRoleBase
)
from ..middleware import require_super_admin, require_platform_manager, get_current_user_org_context
from ..services.rbac_service import OrganizationService, RBACService
from ..auth import get_current_user

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


# --- Organization CRUD ---

@router.post("/", response_model=Organization)
def create_organization(
    org_data: OrganizationBase,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_super_admin)
):
    """Create a new organization (Super Admin only)."""
    return OrganizationService.create_organization(
        name=org_data.name,
        subdomain=org_data.subdomain,
        session=session
    )


@router.get("/", response_model=List[Organization])
def list_organizations(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_platform_manager)
):
    """List all organizations (Platform Manager and above)."""
    # Platform managers see all orgs
    return list(session.exec(select(Organization).where(Organization.is_active == True)).all())


@router.get("/my-organizations", response_model=List[Organization])
def get_my_organizations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get organizations current user has access to."""
    return RBACService.get_user_organizations(current_user, session)


@router.get("/{organization_id}", response_model=Organization)
async def get_organization(
    organization_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get organization details (requires membership)."""
    user, org = await get_current_user_org_context(organization_id, current_user, session)
    return org


# --- User Assignment ---

class UserAssignment(OrganizationBase):
    """Request model for assigning users to organization."""
    user_id: int
    role: str  # UserRoleEnum value


@router.post("/{organization_id}/users", response_model=UserOrganizationRole)
def assign_user_to_organization(
    organization_id: int,
    assignment: UserAssignment,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Assign a user to an organization with a role.
    
    Requires ORG_MANAGER role or higher.
    """
    # Check permission
    user_role = RBACService.get_user_role_in_org(current_user.id, organization_id, session)
    
    if user_role not in [
        UserRoleEnum.SUPER_ADMIN.value,
        UserRoleEnum.PLATFORM_MANAGER.value,
        UserRoleEnum.ORG_MANAGER.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Org Manager access required to assign users"
        )
    
    # Validate role
    try:
        role_enum = UserRoleEnum(assignment.role)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role: {assignment.role}"
        )
    
    return RBACService.assign_user_to_org(
        user_id=assignment.user_id,
        organization_id=organization_id,
        role=role_enum,
        session=session
    )


@router.get("/{organization_id}/users", response_model=List[User])
async def list_organization_users(
    organization_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """List users in an organization."""
    user, org = await get_current_user_org_context(organization_id, current_user, session)
    
    # Get all user-org relationships for this org
    user_org_roles = session.exec(
        select(UserOrganizationRole)
        .where(UserOrganizationRole.organization_id == organization_id)
        .where(UserOrganizationRole.is_active == True)
    ).all()
    
    user_ids = [uor.user_id for uor in user_org_roles]
    if not user_ids:
        return []
    
    users = session.exec(select(User).where(User.id.in_(user_ids))).all()
    return list(users)


@router.delete("/{organization_id}/users/{user_id}")
def remove_user_from_organization(
    organization_id: int,
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Remove a user from an organization."""
    # Check permission
    user_role = RBACService.get_user_role_in_org(current_user.id, organization_id, session)
    
    if user_role not in [
        UserRoleEnum.SUPER_ADMIN.value,
        UserRoleEnum.PLATFORM_MANAGER.value,
        UserRoleEnum.ORG_MANAGER.value
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Org Manager access required to remove users"
        )
    
    # Prevent self-removal
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from organization"
        )
    
    success = RBACService.remove_user_from_org(user_id, organization_id, session)
    
    if not success:
        raise HTTPException(status_code=404, detail="User assignment not found")
    
    return {"message": "User removed from organization"}
