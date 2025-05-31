"""Todo <-> TodoModel 変換責務を集約する Mapper."""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoId,
    TodoTitle,
    TodoDescription,
    TodoStatus,
    TodoDependencies,
)
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.shared.clock import SystemClock

from .todo_model import TodoModel


class TodoMapper:
    """SQLite 用 Todo Data-Mapper."""

    @staticmethod
    def to_entity(todo_row: TodoModel, clock=SystemClock()) -> Todo:
        """DTO → ドメインエンティティ"""
        dependencies = TodoDependencies.empty()
        dependencies = TodoDependencies.from_list(
            [TodoId(UUID(dep_id)) for dep_id in todo_row.dependencies.split(',')]
        )

        return Todo(
            id=TodoId(todo_row.id),
            title=TodoTitle(todo_row.title),
            project_id=ProjectId(todo_row.project_id),
            description=TodoDescription(todo_row.description)
            if todo_row.description
            else None,
            status=TodoStatus(todo_row.status),
            dependencies=dependencies,
            clock=clock,
            created_at=datetime.fromtimestamp(
                todo_row.created_at / 1000, tz=timezone.utc
            ),
            updated_at=datetime.fromtimestamp(
                todo_row.updated_at / 1000, tz=timezone.utc
            ),
            completed_at=datetime.fromtimestamp(
                todo_row.completed_at / 1000, tz=timezone.utc
            )
            if todo_row.completed_at
            else None,
        )

    @staticmethod
    def from_entity(todo: Todo) -> TodoModel:
        """ドメインエンティティ → DTO"""
        dependencies = ','.join(
            [str(dep_id.value) for dep_id in todo.dependencies.values]
        )
        return TodoModel(
            id=todo.id.value,
            project_id=todo.project_id.value,
            title=todo.title.value,
            description=todo.description.value if todo.description else None,
            status=todo.status.value,
            dependencies=dependencies,
            created_at=int(todo.created_at.timestamp() * 1000),
            updated_at=int(todo.updated_at.timestamp() * 1000),
            completed_at=int(todo.completed_at.timestamp() * 1000)
            if todo.completed_at
            else None,
        )
