"""Data Transfer Object for Project entity in SQLite database."""

from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dddpy.domain.project.entities import Project
from dddpy.infrastructure.sqlite.database import Base


class ProjectModel(Base):
    """Data Transfer Object for Project entity in SQLite database."""

    __tablename__ = 'project'
    id: Mapped[UUID] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[int] = mapped_column(index=True, nullable=False)
    updated_at: Mapped[int] = mapped_column(index=True, nullable=False)

    # NOTE: ProjectModel 自体は Mapper 経由でしかエンティティ化しない。
    # 不用意に呼ばれないよう to_entity を削除 or Deprecated 指定にする。

    @staticmethod
    def from_entity(project: Project) -> 'ProjectModel':
        """Convert domain entity to DTO."""
        return ProjectModel(
            id=project.id.value,
            name=project.name.value,
            description=project.description.value,
            created_at=int(project.created_at.timestamp() * 1000),
            updated_at=int(project.updated_at.timestamp() * 1000),
        )
