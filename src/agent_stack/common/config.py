from loguru import logger
from pystonic.conf import BaseAppConfig, BaseModel


class MasterConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8080
    scheduler_url: str = "http://127.0.0.1:8081"


class SchedulerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8081
    agent_nums_weight: float = 0.3
    cpu_weight: float = 0.4
    memory_weight: float = 0.3


class NodeConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8082
    name: str = ""
    master_url: str = "http://127.0.0.1:8080"
    driver: str = "opencode"
    cmd: str = "opencode"
    report_interval: int = 30


class AppConfig(BaseAppConfig):
    master: MasterConfig = MasterConfig()
    scheduler: SchedulerConfig = SchedulerConfig()
    node: NodeConfig = NodeConfig()


CONF = AppConfig()
logger.debug("config loaded: {}", CONF.model_dump(mode="json"))
