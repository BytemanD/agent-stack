import subprocess
import time
from threading import Thread

import httpx
from loguru import logger
from sqlmodel import Session, select

from agent_stack.common.config import CONF
from agent_stack.db.database import engine
from agent_stack.db.models import Agent, AgentStatus, Node, NodeStatus


class NodeManager:
    def create_agent(self, agent: Agent) -> Agent:
        port = self._find_available_port()
        agent.port = port
        agent.status = AgentStatus.running
        self._start_agent_process(agent)
        return agent

    def delete_agent(self, agent: Agent) -> None:
        self._stop_agent_process(agent)

    def _start_agent_process(self, agent: Agent) -> None:
        cmd = CONF.node.cmd
        try:
            subprocess.Popen(
                [cmd, "web", "--port", str(agent.port)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info(f"Started agent {agent.name} on port {agent.port}")
        except Exception as e:
            logger.error(f"Failed to start agent {agent.name}: {e}")
            agent.status = AgentStatus.error

    def _stop_agent_process(self, agent: Agent) -> None:
        logger.info(f"Stopped agent {agent.name}")

    def _find_available_port(self) -> int:
        import socket

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            return s.getsockname()[1]

    def collect_resources(self) -> dict:
        import psutil

        return {
            "cpu_total": float(psutil.cpu_count()),
            "cpu_used": psutil.cpu_percent(interval=1),
            "memory_total": psutil.virtual_memory().total // (1024 * 1024),
            "memory_used": psutil.virtual_memory().used // (1024 * 1024),
        }

    def report_to_master(self) -> None:
        with Session(engine) as session:
            node = session.exec(select(Node).where(Node.name == CONF.node.name)).first()
            if not node:
                logger.warning(f"Node {CONF.node.name} not registered")
                return
            resources = self.collect_resources()
            node.cpu_used = resources["cpu_used"]
            node.memory_used = resources["memory_used"]
            node.status = NodeStatus.online
            session.add(node)
            session.commit()
        try:
            with httpx.Client() as client:
                client.post(
                    f"{CONF.node.master_url}/api/v1/nodes/resources",
                    json={
                        "node_id": node.id,
                        "cpu_total": resources["cpu_total"],
                        "cpu_used": resources["cpu_used"],
                        "memory_total": resources["memory_total"],
                        "memory_used": resources["memory_used"],
                    },
                )
                logger.debug(f"Reported resources to master: {resources}")
        except Exception as e:
            logger.error(f"Failed to report to master: {e}")

    def start_report_loop(self) -> Thread:
        def _loop():
            while True:
                self.report_to_master()
                time.sleep(CONF.node.report_interval)

        thread = Thread(target=_loop, daemon=True)
        thread.start()
        return thread

    def register(self) -> Node:
        with Session(engine) as session:
            node = session.exec(select(Node).where(Node.name == CONF.node.name)).first()
            if not node:
                node = Node(
                    name=CONF.node.name,
                    host=CONF.node.host,
                    port=CONF.node.port,
                    status=NodeStatus.online,
                )
                session.add(node)
            else:
                node.status = NodeStatus.online
            session.commit()
            session.refresh(node)
            logger.info(f"Node registered: {node.name} ({node.id})")
            return node
