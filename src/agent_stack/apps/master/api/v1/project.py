from fastapi import APIRouter, Depends
from sqlmodel import Session

from agent_stack.db.database import get_session
from agent_stack.db.models import Project
from agent_stack.managers.master import MasterManager

router = APIRouter(prefix="/api/v1/projects", tags=["projects"])
manager = MasterManager()


@router.get("")
def list_projects(session: Session = Depends(get_session)):
    projects = manager.list_projects(session)
    return {"projects": [p.model_dump(mode="json") for p in projects]}


@router.post("")
def create_project(name: str, description: str = "", session: Session = Depends(get_session)):
    project = Project(name=name, description=description)
    session.add(project)
    session.commit()
    session.refresh(project)
    return {"project": project.model_dump(mode="json")}
