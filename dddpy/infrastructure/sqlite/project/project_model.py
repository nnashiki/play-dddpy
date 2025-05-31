"""Data Transfer Object for Project entity in SQLite database."""

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dddpy.domain.project.entities import Project
from dddpy.infrastructure.sqlite.database import Base


class ProjectModel(Base):
    """Data Transfer Object for Project entity in SQLite database."""

    # NOTE: ProjectModel 自体は Mapper 経由でしかエンティティ化しない。

    __tablename__ = 'project'
    id: Mapped[UUID] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[int] = mapped_column(index=True, nullable=False)
    updated_at: Mapped[int] = mapped_column(index=True, nullable=False)
