from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlmodel import Session
from ..database import get_session
from ..models.log import Log, LogCreate, LogRead
from ..services import log_service
from ..auth import get_current_user
from ..models import User

router = APIRouter(
    prefix="/api/logs",
    tags=["logs"],
    responses={404: {"description": "Not found"}},
)

@router.post("/", response_model=LogRead, status_code=status.HTTP_201_CREATED)
def create_new_log(log: LogCreate, session: Session = Depends(get_session)):
    """
    Create a new log entry. This is an internal endpoint that could be
    called by other services or scripts.
    """
    # In a multi-tenant system, we might want to associate logs with an organization.
    # For now, we'll allow logs to be created without an organization context.
    created_log = log_service.create_log(session=session, log=log)
    return created_log

@router.get("/", response_model=List[LogRead])
def read_logs(
    skip: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve logs. This should be restricted to authorized users.
    For simplicity, any authenticated user can read logs.
    In a real application, this would be tied to roles and organizations.
    """
    logs = session.query(Log).offset(skip).limit(limit).all()
    return logs
