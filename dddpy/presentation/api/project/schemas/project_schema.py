"""Query model for Project entities in the application."""

from typing import List, Optional
from pydantic import BaseModel, Field

from dddpy.dto.project import ProjectOutputDto


class ProjectSchema(BaseModel):
    """ProjectSchema represents data structure as a read model."""

    id: str = Field(examples=['123e4567-e89b-12d3-a456-426614174000'])
    name: str = Field(examples=['My Project'])
    description: str = Field(examples=['A sample project for demonstration'])
    todos: List[dict] = Field(examples=[[]])
    created_at: int = Field(examples=[1136214245000])
    updated_at: int = Field(examples=[1136214245000])

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True

    @staticmethod
    def from_dto(dto: ProjectOutputDto) -> 'ProjectSchema':
        """Convert a ProjectOutputDto to a ProjectSchema."""
        return ProjectSchema(
            id=dto.id,
            name=dto.name,
            description=dto.description or '',
            todos=[
                {
                    'id': todo.id,
                    'title': todo.title,
                    'description': todo.description or '',
                    'status': todo.status,
                    'dependencies': todo.dependencies,
                    'project_id': dto.id,  # Added for DDD clarity
                    'created_at': int(todo.created_at.timestamp() * 1000),
                    'updated_at': int(todo.updated_at.timestamp() * 1000),
                    'completed_at': int(todo.completed_at.timestamp() * 1000)
                    if todo.completed_at
                    else None,
                }
                for todo in dto.todos
            ],
            created_at=int(dto.created_at.timestamp() * 1000),
            updated_at=int(dto.updated_at.timestamp() * 1000),
        )


class ProjectCreateSchema(BaseModel):
    """ProjectCreateSchema represents data structure as a create model."""

    name: str = Field(min_length=1, max_length=100, examples=['My Project'])
    description: str | None = Field(
        default=None,
        max_length=1000,
        examples=['A sample project for demonstration'],
    )


class AddTodoToProjectSchema(BaseModel):
    """AddTodoToProjectSchema represents data structure for adding Todo to Project."""

    title: str = Field(min_length=1, max_length=100, examples=['Complete the task'])
    description: str | None = Field(
        default=None,
        max_length=1000,
        examples=['Finish implementing the feature'],
    )
    dependencies: List[str] | None = Field(
        default=None,
        examples=[['456e4567-e89b-12d3-a456-426614174001']],
        description='List of Todo IDs that this Todo depends on',
    )
