from fastapi import APIRouter, Depends
from sqlmodel import Session

from agent_stack.db.database import get_session
from agent_stack.managers.master import MasterManager

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])
manager = MasterManager()


@router.get("")
def list_agents(session: Session = Depends(get_session)):
    agents = manager.list_agents(session)
    return {"agents": [a.model_dump(mode="json") for a in agents]}


@router.get("/{agent_id}")
def get_agent(agent_id: int, session: Session = Depends(get_session)):
    agent = manager.get_agent(session, agent_id)
    if not agent:
        return {"error": "agent not found"}, 404
    return {"agent": agent.model_dump(mode="json")}


@router.post("")
def create_agent(
    name: str,
    agent_type: str = "opencode",
    cpu_required: float = 1.0,
    memory_required: int = 512,
    project_id: int | None = None,
    user_id: int | None = None,
    session: Session = Depends(get_session),
):
    agent = manager.create_agent(
        session, name, agent_type, cpu_required, memory_required, project_id, user_id
    )
    return {"agent": agent.model_dump(mode="json")}


@router.delete("/{agent_id}")
def delete_agent(agent_id: int, session: Session = Depends(get_session)):
    ok = manager.delete_agent(session, agent_id)
    if not ok:
        return {"error": "agent not found"}, 404
    return {"message": "deleted"}


@router.post("/{agent_id}/start")
def start_agent(agent_id: int, session: Session = Depends(get_session)):
    agent = manager.start_agent(session, agent_id)
    if not agent:
        return {"error": "agent not found or not stoppable"}, 400
    return {"agent": agent.model_dump(mode="json")}


@router.post("/{agent_id}/stop")
def stop_agent(agent_id: int, session: Session = Depends(get_session)):
    agent = manager.stop_agent(session, agent_id)
    if not agent:
        return {"error": "agent not found or not running"}, 400
    return {"agent": agent.model_dump(mode="json")}
