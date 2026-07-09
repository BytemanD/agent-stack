import uvicorn

from agent_stack.common.config import CONF


def master():
    uvicorn.run(
        "agent_stack.apps.master.main:app",
        host=CONF.master.host,
        port=CONF.master.port,
        reload=True,
    )


def scheduler():
    uvicorn.run(
        "agent_stack.apps.scheduler.main:app",
        host=CONF.scheduler.host,
        port=CONF.scheduler.port,
        reload=True,
    )


def node():
    uvicorn.run(
        "agent_stack.apps.node.main:app",
        host=CONF.node.host,
        port=CONF.node.port,
        reload=True,
    )
