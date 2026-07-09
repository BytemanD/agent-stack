from fastapi import FastAPI
from pydantic import BaseModel
from sqlmodel import Session

from agent_stack.db.database import init_db, get_session
from agent_stack.managers.scheduler import SchedulerManager

manager = SchedulerManager()


class ScheduleRequest(BaseModel):
    agent_type: str = "opencode"
    cpu_required: float = 1.0
    memory_required: int = 512


def create_app() -> FastAPI:
    app = FastAPI(title="AgentStack Scheduler", version="0.1.0")

    @app.on_event("startup")
    def on_startup():
        init_db()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/v1/schedule")
    def schedule(req: ScheduleRequest):
        with Session(next(get_session()).bind) as session:
            node_id = manager.schedule(
                session,
                agent_type=req.agent_type,
                cpu_required=req.cpu_required,
                memory_required=req.memory_required,
            )
            return {"node_id": node_id}

    return app


app = create_app()
