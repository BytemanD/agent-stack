from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlmodel import Session

from agent_stack.db.database import get_session
from agent_stack.managers.master import MasterManager

router = APIRouter(prefix="/api/v1", tags=["service"])
manager = MasterManager()


@router.get("/nodes")
def list_nodes(session: Session = Depends(get_session)):
    nodes = manager.list_nodes(session)
    return {"nodes": [n.model_dump(mode="json") for n in nodes]}


class ResourceReport(BaseModel):
    node_id: int
    cpu_total: float = 0
    cpu_used: float = 0
    memory_total: int = 0
    memory_used: int = 0


@router.post("/nodes/resources")
def report_resources(report: ResourceReport, session: Session = Depends(get_session)):
    manager.report_node_resources(
        session,
        node_id=report.node_id,
        cpu_used=report.cpu_used,
        memory_used=report.memory_used,
        cpu_total=report.cpu_total,
        memory_total=report.memory_total,
    )
    return {"message": "ok"}
