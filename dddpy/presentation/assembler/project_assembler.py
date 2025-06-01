"""ProjectAssembler for converting between Project DTOs and Schemas."""

from dddpy.dto.project import ProjectOutputDto
from dddpy.presentation.api.project.schemas.project_schema import ProjectSchema
from dddpy.presentation.assembler.project_todo_assembler import ProjectTodoAssembler


class ProjectAssembler:
    """ProjectOutputDto ⇨ ProjectSchema 変換責務"""

    @staticmethod
    def to_schema(dto: ProjectOutputDto) -> ProjectSchema:
        return ProjectSchema(
            id=dto.id,
            name=dto.name,
            description=dto.description or '',
            todos=[
                ProjectTodoAssembler.to_schema(todo_dto, dto.id)
                for todo_dto in dto.todos
            ],
            created_at=int(dto.created_at.timestamp() * 1000),
            updated_at=int(dto.updated_at.timestamp() * 1000),
        )
