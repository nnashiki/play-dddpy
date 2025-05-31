"""Data Transfer Object for Todo entity in SQLite database."""

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dddpy.infrastructure.sqlite.database import Base


class TodoModel(Base):
    """Data Transfer Object for Todo entity in SQLite database."""

    __tablename__ = 'todo'
    id: Mapped[UUID] = mapped_column(primary_key=True, autoincrement=False)
    project_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(index=True, nullable=False)
    dependencies: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[int] = mapped_column(index=True, nullable=False)
    updated_at: Mapped[int] = mapped_column(index=True, nullable=False)
    completed_at: Mapped[int] = mapped_column(index=True, nullable=True)
