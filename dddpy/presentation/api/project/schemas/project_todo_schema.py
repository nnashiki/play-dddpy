"""Todo schemas for Project API endpoints."""

from typing import List
from pydantic import BaseModel, Field

from dddpy.domain.todo.entities import Todo
from dddpy.dto.todo import TodoOutputDto


class ProjectTodoSchema(BaseModel):
    """ProjectTodoSchema represents Todo data structure in Project context."""

    id: str = Field(examples=['123e4567-e89b-12d3-a456-426614174000'])
    title: str = Field(examples=['Complete the project'])
    description: str = Field(examples=['Finish implementing the DDD architecture'])
    status: str = Field(examples=['not_started'])
    dependencies: List[str] = Field(examples=[['456e4567-e89b-12d3-a456-426614174001']])
    project_id: str = Field(
        examples=['789e4567-e89b-12d3-a456-426614174002']
    )  # Added for clarity
    created_at: int = Field(examples=[1136214245000])
    updated_at: int = Field(examples=[1136214245000])
    completed_at: int | None = Field(examples=[1136214245000])

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True

    @staticmethod
    def from_dto(dto: TodoOutputDto, project_id: str) -> 'ProjectTodoSchema':
        """Convert a TodoOutputDto to a ProjectTodoSchema."""
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


class ProjectTodoUpdateSchema(BaseModel):
    """ProjectTodoUpdateSchema represents data structure for updating Todo in Project context."""

    title: str = Field(min_length=1, max_length=100, examples=['Complete the project'])
    description: str | None = Field(
        default=None,
        max_length=1000,
        examples=['Finish implementing the DDD architecture'],
    )
    dependencies: List[str] | None = Field(
        default=None,
        examples=[['456e4567-e89b-12d3-a456-426614174001']],
        description='List of Todo IDs that this Todo depends on',
    )
