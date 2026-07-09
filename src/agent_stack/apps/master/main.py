from fastapi import FastAPI

from agent_stack.db.database import init_db

from .api.v1 import agent, project, service, user


def create_app() -> FastAPI:
    app = FastAPI(title="AgentStack Master", version="0.1.0")
    app.include_router(agent.router)
    app.include_router(user.router)
    app.include_router(project.router)
    app.include_router(service.router)

    @app.on_event("startup")
    def on_startup():
        init_db()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
