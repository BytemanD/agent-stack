from pystonic.conf import BaseAppConfig, BaseModel


class MasterConfig(BaseModel):
    pass


class SchedulerConfig(BaseModel):
    pass


class NodeConfig(BaseModel):
    pass


class AppConfig(BaseAppConfig):
    master: MasterConfig = MasterConfig()
    scheduler: SchedulerConfig = SchedulerConfig()
    node: NodeConfig = NodeConfig()


CONF = AppConfig()
