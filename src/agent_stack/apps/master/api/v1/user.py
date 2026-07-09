from fastapi import APIRouter, Depends
from sqlmodel import Session

from agent_stack.db.database import get_session
from agent_stack.db.models import User
from agent_stack.managers.master import MasterManager

router = APIRouter(prefix="/api/v1/users", tags=["users"])
manager = MasterManager()


@router.get("")
def list_users(session: Session = Depends(get_session)):
    users = manager.list_users(session)
    return {"users": [u.model_dump(mode="json") for u in users]}


@router.post("")
def create_user(username: str, email: str = "", session: Session = Depends(get_session)):
    user = User(username=username, email=email)
    session.add(user)
    session.commit()
    session.refresh(user)
    return {"user": user.model_dump(mode="json")}
