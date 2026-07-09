import httpx
import typer
from rich.console import Console
from sqlmodel import Session, select

from agent_stack.db.database import engine, init_db
from agent_stack.db.models import Agent, Node, Project, User

app = typer.Typer(name="agentstack", help="AgentStack management CLI")
console = Console()

# -- service group --
service_app = typer.Typer(name="service", help="Service management commands")
app.add_typer(service_app)


@service_app.command("list")
def service_list():
    """List all services and their status"""
    init_db()
    with Session(engine) as session:
        nodes = session.exec(select(Node)).all()
        agents = session.exec(select(Agent)).all()
    from rich.table import Table

    table = Table(title="Services")
    table.add_column("Type", style="cyan")
    table.add_column("Count", style="green")
    table.add_row("Nodes", str(len(nodes)))
    table.add_row("Agents", str(len(agents)))
    console.print(table)


# -- user group --
user_app = typer.Typer(name="user", help="User management commands")
app.add_typer(user_app)


@user_app.command("list")
def user_list():
    """List all users"""
    init_db()
    with Session(engine) as session:
        users = session.exec(select(User)).all()
    if not users:
        console.print("No users found")
        return
    from rich.table import Table

    table = Table(title="Users")
    table.add_column("ID", style="cyan")
    table.add_column("Username", style="green")
    table.add_column("Email")
    table.add_column("Created")
    for u in users:
        table.add_row(str(u.id), u.username, u.email, str(u.created_at))
    console.print(table)


# -- project group --
project_app = typer.Typer(name="project", help="Project management commands")
app.add_typer(project_app)


@project_app.command("list")
def project_list():
    """List all projects"""
    init_db()
    with Session(engine) as session:
        projects = session.exec(select(Project)).all()
    if not projects:
        console.print("No projects found")
        return
    from rich.table import Table

    table = Table(title="Projects")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Description")
    table.add_column("Created")
    for p in projects:
        table.add_row(str(p.id), p.name, p.description, str(p.created_at))
    console.print(table)


# -- agent group --
agent_app = typer.Typer(name="agent", help="Agent management commands")
app.add_typer(agent_app)


@agent_app.command("list")
def agent_list():
    """List all agents"""
    init_db()
    with Session(engine) as session:
        agents = session.exec(select(Agent)).all()
    if not agents:
        console.print("No agents found")
        return
    from rich.table import Table

    table = Table(title="Agents")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Type")
    table.add_column("Status")
    table.add_column("Node ID")
    table.add_column("Port")
    for a in agents:
        table.add_row(
            str(a.id), a.name, a.agent_type, a.status.value, str(a.node_id or ""), str(a.port or "")
        )
    console.print(table)


@agent_app.command("create")
def agent_create(
    name: str = typer.Argument(help="Agent name"),
    agent_type: str = typer.Option("opencode", "--type", "-t", help="Agent type"),
    cpu: float = typer.Option(1.0, "--cpu", help="CPU cores required"),
    memory: int = typer.Option(512, "--memory", "-m", help="Memory MB required"),
):
    """Create a new agent"""
    try:
        resp = httpx.post(
            "http://127.0.0.1:8080/api/v1/agents",
            params={
                "name": name,
                "agent_type": agent_type,
                "cpu_required": cpu,
                "memory_required": memory,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        console.print(f"Agent created: {data['agent']['name']} (ID: {data['agent']['id']})")
    except Exception as e:
        console.print(f"Failed to create agent: {e}", style="red")


@agent_app.command("delete")
def agent_delete(
    agent_id: int = typer.Argument(help="Agent ID"),
):
    """Delete an agent"""
    try:
        resp = httpx.delete(f"http://127.0.0.1:8080/api/v1/agents/{agent_id}", timeout=10)
        resp.raise_for_status()
        console.print(f"Agent {agent_id} deleted")
    except Exception as e:
        console.print(f"Failed to delete agent: {e}", style="red")


def main():
    app()
