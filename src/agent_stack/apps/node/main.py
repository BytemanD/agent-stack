from fastapi import FastAPI
from sqlmodel import Session

from agent_stack.db.database import init_db, get_session
from agent_stack.db.models import Agent
from agent_stack.managers.node import NodeManager

manager = NodeManager()


def create_app() -> FastAPI:
    app = FastAPI(title="AgentStack Node", version="0.1.0")

    @app.on_event("startup")
    def on_startup():
        init_db()
        manager.register()
        manager.start_report_loop()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/api/v1/agents")
    def create_agent(data: dict):
        agent = Agent(**{k: v for k, v in data.items() if k in Agent.model_fields})
        agent = manager.create_agent(agent)
        return agent.model_dump(mode="json")

    @app.delete("/api/v1/agents/{agent_id}")
    def delete_agent(agent_id: int):
        with Session(next(get_session()).bind) as session:
            agent = session.get(Agent, agent_id)
            if agent:
                manager.delete_agent(agent)
            return {"message": "ok"}

    return app


app = create_app()
