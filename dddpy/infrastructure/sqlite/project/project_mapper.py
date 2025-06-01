"""Project <-> ProjectModel 変換責務を集約する Mapper."""

from datetime import UTC, datetime

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)
from dddpy.domain.shared.clock import SystemClock
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import TodoId

from ..todo.todo_model import TodoModel
from ..todo.todo_mapper import TodoMapper
from .project_model import ProjectModel


class ProjectMapper:
    """SQLite 用 Project Data-Mapper."""

    @staticmethod
    def to_entity(
        project_row: ProjectModel,
        todo_rows: list[TodoModel],
        clock=SystemClock(),
    ) -> Project:
        """DTO → ドメインエンティティ（集約完成形で返す）"""
        todos_dict: dict[TodoId, Todo] = {
            TodoId(t.id): TodoMapper.to_entity(t, clock) for t in todo_rows
        }

        return Project(
            id=ProjectId(project_row.id),
            name=ProjectName(project_row.name),
            description=ProjectDescription(project_row.description),
            todos=todos_dict,
            clock=clock,
            created_at=datetime.fromtimestamp(project_row.created_at / 1000, tz=UTC),
            updated_at=datetime.fromtimestamp(project_row.updated_at / 1000, tz=UTC),
        )

    @staticmethod
    def from_entity(project: Project) -> ProjectModel:
        """ドメインエンティティ → DTO"""
        return ProjectModel(
            id=project.id.value,
            name=project.name.value,
            description=project.description.value,
            created_at=int(project.created_at.timestamp() * 1000),
            updated_at=int(project.updated_at.timestamp() * 1000),
        )
