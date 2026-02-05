from sqlmodel import Session
from ..models.log import Log, LogCreate

def create_log(session: Session, log: LogCreate) -> Log:
    """
    Creates a new log entry in the database.
    """
    db_log = Log.model_validate(log)
    session.add(db_log)
    session.commit()
    session.refresh(db_log)
    return db_log
