"""ProjectTodoAssembler for converting DTOs to schemas."""

from dddpy.dto.todo import TodoOutputDto
from dddpy.presentation.api.project.schemas.project_todo_schema import ProjectTodoSchema


class ProjectTodoAssembler:
    """TodoOutputDto → ProjectTodoSchema 変換のみ（Presentation 層）"""

    @staticmethod
    def to_schema(dto: TodoOutputDto, project_id: str) -> ProjectTodoSchema:
        """
        TodoOutputDto から ProjectTodoSchema を生成

        Args:
            dto: 変換対象のTodoOutputDto
            project_id: プロジェクトID（文字列）

        Returns:
            ProjectTodoSchema: プレゼンテーション層用のTodoスキーマ
        """
        return ProjectTodoSchema(
            id=dto.id,
            title=dto.title,
            description=dto.description or '',
            status=dto.status,
            dependencies=dto.dependencies,
            project_id=project_id,
            created_at=int(dto.created_at.timestamp() * 1000),
            updated_at=int(dto.updated_at.timestamp() * 1000),
            completed_at=int(dto.completed_at.timestamp() * 1000)
            if dto.completed_at
            else None,
        )
