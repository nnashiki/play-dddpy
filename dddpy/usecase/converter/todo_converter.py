"""Todo ⇄ TodoOutputDto 変換責務（Application 層）"""

from uuid import UUID

from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.shared.clock import SystemClock
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription,
    TodoId,
    TodoStatus,
    TodoTitle,
)
from dddpy.dto.todo import TodoOutputDto


class TodoConverter:
    """Todo ⇄ TodoOutputDto"""

    # ---------- Domain -> DTO ---------- #
    @staticmethod
    def to_output_dto(todo: Todo) -> TodoOutputDto:
        return TodoOutputDto(
            id=str(todo.id.value),
            title=todo.title.value,
            description=todo.description.value if todo.description else None,
            status=todo.status.value,
            dependencies=[str(dep.value) for dep in todo.dependencies.values],
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            completed_at=todo.completed_at,
        )

    # ---------- DTO -> Domain ---------- #
    @staticmethod
    def from_output_dto(dto: TodoOutputDto, project_id: str) -> Todo:
        return Todo(
            id=TodoId(UUID(dto.id)),
            title=TodoTitle(dto.title),
            project_id=ProjectId(UUID(project_id)),
            description=TodoDescription(dto.description) if dto.description else None,
            status=TodoStatus(dto.status),
            dependencies=TodoDependencies.from_list(
                [TodoId(UUID(dep)) for dep in dto.dependencies]
            ),
            clock=SystemClock(),
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            completed_at=dto.completed_at,
        )
