from collections.abc import Generator

from sqlmodel import Session, SQLModel, create_engine

from agent_stack.common.config import CONF

engine = create_engine(
    CONF.db.url,
    echo=CONF.db.echo,
    pool_size=CONF.db.pool_size,
    max_overflow=CONF.db.max_overflow,
    pool_recycle=CONF.db.pool_recycle,
)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
