import httpx
from loguru import logger
from sqlmodel import Session, select

from agent_stack.common.config import CONF
from agent_stack.db.database import engine
from agent_stack.db.models import Agent, AgentStatus, Node, NodeStatus, Project, User


class MasterManager:
    def list_agents(self, session: Session) -> list[Agent]:
        return list(session.exec(select(Agent)).all())

    def get_agent(self, session: Session, agent_id: int) -> Agent | None:
        return session.get(Agent, agent_id)

    def create_agent(
        self,
        session: Session,
        name: str,
        agent_type: str = "opencode",
        cpu_required: float = 1.0,
        memory_required: int = 512,
        project_id: int | None = None,
        user_id: int | None = None,
    ) -> Agent:
        node_id = self._schedule(session, agent_type, cpu_required, memory_required)
        agent = Agent(
            name=name,
            agent_type=agent_type,
            node_id=node_id,
            cpu_required=cpu_required,
            memory_required=memory_required,
            project_id=project_id,
            user_id=user_id,
            status=AgentStatus.creating,
        )
        session.add(agent)
        session.commit()
        session.refresh(agent)
        if node_id:
            self._deploy_to_node(agent, node_id)
        session.refresh(agent)
        return agent

    def delete_agent(self, session: Session, agent_id: int) -> bool:
        agent = session.get(Agent, agent_id)
        if not agent:
            return False
        if agent.node_id:
            self._notify_node_delete(agent)
        session.delete(agent)
        session.commit()
        return True

    def start_agent(self, session: Session, agent_id: int) -> Agent | None:
        agent = session.get(Agent, agent_id)
        if not agent or agent.status != AgentStatus.stopped:
            return None
        agent.status = AgentStatus.running
        session.add(agent)
        session.commit()
        session.refresh(agent)
        return agent

    def stop_agent(self, session: Session, agent_id: int) -> Agent | None:
        agent = session.get(Agent, agent_id)
        if not agent or agent.status != AgentStatus.running:
            return None
        agent.status = AgentStatus.stopped
        session.add(agent)
        session.commit()
        session.refresh(agent)
        return agent

    def list_nodes(self, session: Session) -> list[Node]:
        return list(session.exec(select(Node)).all())

    def report_node_resources(
        self,
        session: Session,
        node_id: int,
        cpu_used: float,
        memory_used: int,
        cpu_total: float = 0,
        memory_total: int = 0,
    ) -> None:
        node = session.get(Node, node_id)
        if not node:
            logger.warning(f"Node {node_id} not found for resource report")
            return
        node.cpu_used = cpu_used
        node.memory_used = memory_used
        if cpu_total:
            node.cpu_total = cpu_total
        if memory_total:
            node.memory_total = memory_total
        node.status = NodeStatus.online
        session.add(node)
        session.commit()

    def list_users(self, session: Session) -> list[User]:
        return list(session.exec(select(User)).all())

    def list_projects(self, session: Session) -> list[Project]:
        return list(session.exec(select(Project)).all())

    def _schedule(
        self,
        session: Session,
        agent_type: str,
        cpu_required: float,
        memory_required: int,
    ) -> int | None:
        try:
            resp = httpx.post(
                f"{CONF.master.scheduler_url}/api/v1/schedule",
                json={
                    "agent_type": agent_type,
                    "cpu_required": cpu_required,
                    "memory_required": memory_required,
                },
                timeout=10,
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("node_id")
        except Exception as e:
            logger.error(f"Schedule failed: {e}")
            return None

    def _deploy_to_node(self, agent: Agent, node_id: int) -> None:
        with Session(engine) as session:
            node = session.get(Node, node_id)
        if not node:
            logger.error(f"Node {node_id} not found")
            return
        try:
            resp = httpx.post(
                f"http://{node.host}:{node.port}/api/v1/agents",
                json=agent.model_dump(mode="json"),
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            with Session(engine) as session:
                db_agent = session.get(Agent, agent.id)
                if db_agent:
                    db_agent.status = AgentStatus(data.get("status", "running"))
                    db_agent.port = data.get("port")
                    session.add(db_agent)
                    session.commit()
        except Exception as e:
            logger.error(f"Deploy to node {node_id} failed: {e}")
            with Session(engine) as session:
                db_agent = session.get(Agent, agent.id)
                if db_agent:
                    db_agent.status = AgentStatus.error
                    session.add(db_agent)
                    session.commit()

    def _notify_node_delete(self, agent: Agent) -> None:
        with Session(engine) as session:
            node = session.get(Node, agent.node_id)
        if not node:
            return
        try:
            httpx.delete(
                f"http://{node.host}:{node.port}/api/v1/agents/{agent.id}",
                timeout=10,
            )
        except Exception as e:
            logger.error(f"Notify node delete failed: {e}")
