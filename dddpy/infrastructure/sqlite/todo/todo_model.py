"""Data Transfer Object for Todo entity in SQLite database."""

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription,
    TodoId,
    TodoStatus,
    TodoTitle,
)
from dddpy.infrastructure.sqlite.database import Base


class TodoModel(Base):
    """Data Transfer Object for Todo entity in SQLite database."""

    __tablename__ = 'todo'
    id: Mapped[UUID] = mapped_column(primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(index=True, nullable=False)
    dependencies: Mapped[str] = mapped_column(nullable=True)
    created_at: Mapped[int] = mapped_column(index=True, nullable=False)
    updated_at: Mapped[int] = mapped_column(index=True, nullable=False)
    completed_at: Mapped[int] = mapped_column(index=True, nullable=True)

    def to_entity(self) -> Todo:
        """Convert DTO to domain entity."""
        # Parse dependencies from JSON
        dependencies = TodoDependencies.empty()
        if (
            self.dependencies and self.dependencies.strip()
        ):  # Check for non-empty string
            try:
                dep_uuids = json.loads(self.dependencies)
                if isinstance(dep_uuids, list):  # Ensure it's a list
                    dep_ids = [
                        TodoId(UUID(uuid_str)) for uuid_str in dep_uuids if uuid_str
                    ]
                    dependencies = TodoDependencies.from_list(dep_ids)
                else:
                    logging.warning(
                        f'Dependencies data is not a list: {self.dependencies}'
                    )
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                # Log the error instead of silently ignoring it
                logging.warning(
                    f'Failed to parse dependencies JSON: {self.dependencies}, error: {e}'
                )
                dependencies = TodoDependencies.empty()

        return Todo(
            TodoId(self.id),
            TodoTitle(self.title),
            TodoDescription(self.description) if self.description else None,
            TodoStatus(self.status),
            dependencies,
            datetime.fromtimestamp(self.created_at / 1000, tz=timezone.utc),
            datetime.fromtimestamp(self.updated_at / 1000, tz=timezone.utc),
            datetime.fromtimestamp(self.completed_at / 1000, tz=timezone.utc)
            if self.completed_at
            else None,
        )

    @staticmethod
    def from_entity(todo: Todo) -> 'TodoModel':
        """Convert domain entity to DTO."""
        # Convert dependencies to JSON
        dependencies_json = None
        if not todo.dependencies.is_empty():
            dep_uuids = [str(dep_id.value) for dep_id in todo.dependencies.values]
            dependencies_json = json.dumps(dep_uuids) if dep_uuids else None

        return TodoModel(
            id=todo.id.value,
            title=todo.title.value,
            description=todo.description.value if todo.description else None,
            status=todo.status.value,
            dependencies=dependencies_json,  # This will be None if empty, not empty string
            created_at=int(todo.created_at.timestamp() * 1000),
            updated_at=int(todo.updated_at.timestamp() * 1000),
            completed_at=int(todo.completed_at.timestamp() * 1000)
            if todo.completed_at
            else None,
        )
