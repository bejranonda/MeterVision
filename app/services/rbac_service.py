"""Organization and RBAC service layer."""
from typing import List, Optional
from sqlmodel import Session, select
from fastapi import HTTPException, status

from ..models import (
    Organization, OrganizationSettings,
    User, UserOrganizationRole, UserRoleEnum
)


class RBACService:
    """Service for managing roles and permissions."""
    
    @staticmethod
    def assign_user_to_org(
        user_id: int,
        organization_id: int,
        role: UserRoleEnum,
        session: Session
    ) -> UserOrganizationRole:
        """
        Assign a user to an organization with a specific role.
        
        Args:
            user_id: The user ID
            organization_id: The organization ID
            role: The role to assign
            session: Database session
        
        Returns:
            The created UserOrganizationRole
        
        Raises:
            HTTPException: If user or organization doesn't exist
        """
        # Verify user exists
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Verify organization exists
        org = session.get(Organization, organization_id)
        if not org:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Check if assignment already exists
        existing = session.exec(
            select(UserOrganizationRole)
            .where(UserOrganizationRole.user_id == user_id)
            .where(UserOrganizationRole.organization_id == organization_id)
        ).first()
        
        if existing:
            # Update existing assignment
            existing.role = role.value
            existing.is_active = True
            session.add(existing)
            session.commit()
            session.refresh(existing)
            return existing
        
        # Create new assignment
        user_org_role = UserOrganizationRole(
            user_id=user_id,
            organization_id=organization_id,
            role=role.value,
            is_active=True
        )
        session.add(user_org_role)
        session.commit()
        session.refresh(user_org_role)
        return user_org_role
    
    @staticmethod
    def remove_user_from_org(
        user_id: int,
        organization_id: int,
        session: Session
    ) -> bool:
        """
        Remove a user from an organization (soft delete).
        
        Args:
            user_id: The user ID
            organization_id: The organization ID
            session: Database session
        
        Returns:
            True if removed, False if not found
        """
        user_org_role = session.exec(
            select(UserOrganizationRole)
            .where(UserOrganizationRole.user_id == user_id)
            .where(UserOrganizationRole.organization_id == organization_id)
        ).first()
        
        if not user_org_role:
            return False
        
        user_org_role.is_active = False
        session.add(user_org_role)
        session.commit()
        return True
    
    @staticmethod
    def get_user_organizations(user: User, session: Session) -> List[Organization]:
        """
        Get all organizations a user has access to.
        
        Args:
            user: The user
            session: Database session
        
        Returns:
            List of organizations
        """
        # Super admin sees all orgs
        if user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
            return list(session.exec(select(Organization).where(Organization.is_active == True)).all())
        
        # Get orgs user is assigned to
        user_org_roles = session.exec(
            select(UserOrganizationRole)
            .where(UserOrganizationRole.user_id == user.id)
            .where(UserOrganizationRole.is_active == True)
        ).all()
        
        org_ids = [uor.organization_id for uor in user_org_roles]
        if not org_ids:
            return []
        
        return list(session.exec(
            select(Organization)
            .where(Organization.id.in_(org_ids))
            .where(Organization.is_active == True)
        ).all())
    
    @staticmethod
    def get_user_role_in_org(
        user_id: int,
        organization_id: int,
        session: Session
    ) -> Optional[str]:
        """
        Get a user's role in a specific organization.
        
        Args:
            user_id: The user ID
            organization_id: The organization ID
            session: Database session
        
        Returns:
            The role string or None if not found
        """
        user = session.get(User, user_id)
        if not user:
            return None
        
        # Super admin is always super admin
        if user.platform_role == UserRoleEnum.SUPER_ADMIN.value:
            return UserRoleEnum.SUPER_ADMIN.value
        
        user_org_role = session.exec(
            select(UserOrganizationRole)
            .where(UserOrganizationRole.user_id == user_id)
            .where(UserOrganizationRole.organization_id == organization_id)
            .where(UserOrganizationRole.is_active == True)
        ).first()
        
        return user_org_role.role if user_org_role else None


class OrganizationService:
    """Service for managing organizations."""
    
    @staticmethod
    def create_organization(
        name: str,
        subdomain: Optional[str],
        session: Session
    ) -> Organization:
        """
        Create a new organization.
        
        Args:
            name: Organization name
            subdomain: Optional subdomain
            session: Database session
        
        Returns:
            The created Organization
        
        Raises:
            HTTPException: If subdomain is already taken
        """
        # Check subdomain uniqueness
        if subdomain:
            existing = session.exec(
                select(Organization).where(Organization.subdomain == subdomain)
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Subdomain already taken"
                )
        
        org = Organization(
            name=name,
            subdomain=subdomain,
            is_active=True,
            billing_status="trial"
        )
        session.add(org)
        session.commit()
        session.refresh(org)
        
        # Create default settings
        settings = OrganizationSettings(
            organization_id=org.id,
            settings_json="{}"
        )
        session.add(settings)
        session.commit()
        
        return org
