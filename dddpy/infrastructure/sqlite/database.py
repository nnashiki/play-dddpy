"""Database configuration and session management for SQLite."""

from typing import Any
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = 'sqlite:///./db/sqlite.db'

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={
        'check_same_thread': False,
    },
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=True,
)


Base: Any = declarative_base()


def create_tables():
    """Create all database tables defined in SQLAlchemy models."""
    # Import all models to ensure they are registered with SQLAlchemy
    from dddpy.infrastructure.sqlite.project.project_model import ProjectModel
    from dddpy.infrastructure.sqlite.project.project_history_model import (
        ProjectHistoryModel,
    )
    from dddpy.infrastructure.sqlite.todo.todo_model import TodoModel
    from dddpy.infrastructure.sqlite.todo.todo_history_model import TodoHistoryModel
    from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel

    Base.metadata.create_all(bind=engine)


def reset_database():
    """Reset database by dropping and recreating all tables."""
    # Import all models to ensure they are registered with SQLAlchemy
    from dddpy.infrastructure.sqlite.project.project_model import ProjectModel
    from dddpy.infrastructure.sqlite.project.project_history_model import (
        ProjectHistoryModel,
    )
    from dddpy.infrastructure.sqlite.todo.todo_model import TodoModel
    from dddpy.infrastructure.sqlite.todo.todo_history_model import TodoHistoryModel
    from dddpy.infrastructure.sqlite.outbox.outbox_model import OutboxModel

    # Drop all tables and recreate them
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
