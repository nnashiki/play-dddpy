"""Data Transfer Object for Project entity in SQLite database."""

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.shared.clock import SystemClock
from dddpy.infrastructure.sqlite.database import Base


class ProjectModel(Base):
    """Data Transfer Object for Project entity in SQLite database."""

    __tablename__ = 'project'
    id: Mapped[UUID] = mapped_column(primary_key=True, autoincrement=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[int] = mapped_column(index=True, nullable=False)
    updated_at: Mapped[int] = mapped_column(index=True, nullable=False)

    def to_entity(self) -> Project:
        """Convert DTO to domain entity."""
        return Project.from_persistence(
            ProjectId(self.id),
            self.name,
            self.description,
            {},  # todos will be loaded separately
            datetime.fromtimestamp(self.created_at / 1000, tz=timezone.utc),
            datetime.fromtimestamp(self.updated_at / 1000, tz=timezone.utc),
            SystemClock(),
        )

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
