"""ProjectTodoAssembler for converting between Todo entities and DTOs."""

from uuid import UUID
from typing import Optional

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoId,
    TodoTitle,
    TodoDescription,
    TodoStatus,
    TodoDependencies,
)
from dddpy.domain.project.value_objects import ProjectId
from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.shared.clock import SystemClock


class ProjectTodoAssembler:
    """TodoエンティティとDTO間の変換責務を担う Assembler"""

    @staticmethod
    def to_output_dto(todo: Todo) -> TodoOutputDto:
        """
        Todoエンティティから API 出力用の TodoOutputDto を生成

        Args:
            todo: 変換対象のTodoエンティティ

        Returns:
            TodoOutputDto: API出力用のDTO
        """
        return TodoOutputDto(
            id=str(todo.id.value),
            title=todo.title.value,
            description=todo.description.value if todo.description else None,
            status=todo.status.value,
            dependencies=[str(dep_id.value) for dep_id in todo.dependencies.values],
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            completed_at=todo.completed_at,
        )

    @staticmethod
    def from_dto(dto: TodoOutputDto, project_id: str) -> Todo:
        """
        DTO を受け取り、ドメインエンティティ Todo を生成（主にテストや再構築用）

        Args:
            dto: 変換元のTodoOutputDto
            project_id: プロジェクトID（文字列）

        Returns:
            Todo: 再構築されたTodoエンティティ
        """
        return Todo(
            id=TodoId(UUID(dto.id)),
            title=TodoTitle(dto.title),
            project_id=ProjectId(UUID(project_id)),
            description=TodoDescription(dto.description) if dto.description else None,
            status=TodoStatus(dto.status),
            dependencies=TodoDependencies.from_list(
                [TodoId(UUID(dep_id)) for dep_id in dto.dependencies]
            ),
            clock=SystemClock(),
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            completed_at=dto.completed_at,
        )
