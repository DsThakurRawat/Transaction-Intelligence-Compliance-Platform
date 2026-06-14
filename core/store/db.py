from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from core.config import get_settings
from core.store.models import Base


def make_engine(url: str) -> Engine:
    # check_same_thread=False is the standard SQLite-with-SQLAlchemy setting.
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=connect_args)


# The app-wide engine + session factory, built from config.
engine: Engine = make_engine(get_settings().database_url)
SessionLocal = sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


def init_db(target_engine: Engine | None = None) -> None:
    """Create tables if they don't exist."""
    Base.metadata.create_all(target_engine or engine)
