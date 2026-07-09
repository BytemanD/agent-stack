from sqlmodel import Session, select

from agent_stack.common.config import CONF
from agent_stack.db.models import Node, NodeStatus


class SchedulerManager:
    def schedule(
        self,
        session: Session,
        agent_type: str = "opencode",
        cpu_required: float = 1.0,
        memory_required: int = 512,
    ) -> int | None:
        candidates = self._filter(session, agent_type, cpu_required, memory_required)
        if not candidates:
            return None
        return self._weight(candidates)

    def _filter(
        self,
        session: Session,
        agent_type: str,
        cpu_required: float,
        memory_required: int,
    ) -> list[Node]:
        nodes = session.exec(select(Node).where(Node.status == NodeStatus.online)).all()
        result = []
        for node in nodes:
            cpu_avail = 100.0 - node.cpu_used
            mem_avail = node.memory_total - node.memory_used
            if cpu_avail >= cpu_required and mem_avail >= memory_required:
                result.append(node)
        return result

    def _weight(self, nodes: list[Node]) -> int:
        if len(nodes) == 1:
            return nodes[0].id

        cpu_w = CONF.scheduler.cpu_weight
        mem_w = CONF.scheduler.memory_weight
        agent_w = CONF.scheduler.agent_nums_weight

        max_cpu_avail = max(100.0 - n.cpu_used for n in nodes) or 1
        max_mem_avail = max(n.memory_total - n.memory_used for n in nodes) or 1
        min_agent_count = min(n.agent_count for n in nodes) or 1
        max_agent_count = max(n.agent_count for n in nodes) or 1

        best_node = None
        best_score = -1.0

        for node in nodes:
            cpu_avail = 100.0 - node.cpu_used
            mem_avail = node.memory_total - node.memory_used
            cpu_score = cpu_avail / max_cpu_avail
            mem_score = mem_avail / max_mem_avail
            if max_agent_count == min_agent_count:
                agent_score = 1.0
            else:
                agent_score = 1.0 - (node.agent_count - min_agent_count) / (
                    max_agent_count - min_agent_count
                )
            score = cpu_w * cpu_score + mem_w * mem_score + agent_w * agent_score
            if score > best_score:
                best_score = score
                best_node = node.id

        return best_node
