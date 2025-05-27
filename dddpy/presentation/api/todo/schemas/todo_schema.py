"""Query model for Todo entities in the application."""

from typing import List
from pydantic import BaseModel, Field

from dddpy.domain.todo.entities import Todo
from dddpy.dto.todo import TodoOutputDto


class TodoSchema(BaseModel):
    """TodoQueryModel represents data structure as a read model."""

    id: str = Field(examples=['123e4567-e89b-12d3-a456-426614174000'])
    title: str = Field(examples=['Complete the project'])
    description: str = Field(examples=['Finish implementing the DDD architecture'])
    status: str = Field(examples=['not_started'])
    dependencies: List[str] = Field(examples=[['456e4567-e89b-12d3-a456-426614174001']])
    created_at: int = Field(examples=[1136214245000])
    updated_at: int = Field(examples=[1136214245000])
    completed_at: int | None = Field(examples=[1136214245000])

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True

    @staticmethod
    def from_entity(todo: Todo) -> 'TodoSchema':
        """Convert a Todo entity to a TodoQueryModel."""
        return TodoSchema(
            id=str(todo.id.value),
            title=todo.title.value if todo.title else '',
            description=todo.description.value if todo.description else '',
            status=todo.status.value,
            dependencies=[str(dep_id.value) for dep_id in todo.dependencies.values],
            created_at=int(todo.created_at.timestamp() * 1000),
            updated_at=int(todo.updated_at.timestamp() * 1000),
            completed_at=int(todo.completed_at.timestamp() * 1000)
            if todo.completed_at
            else None,
        )

    @staticmethod
    def from_dto(dto: TodoOutputDto) -> 'TodoSchema':
        """Convert a TodoOutputDto to a TodoSchema."""
        return TodoSchema(
            id=dto.id,
            title=dto.title,
            description=dto.description or '',
            status=dto.status,
            dependencies=dto.dependencies,
            created_at=int(dto.created_at.timestamp() * 1000),
            updated_at=int(dto.updated_at.timestamp() * 1000),
            completed_at=int(dto.completed_at.timestamp() * 1000)
            if dto.completed_at
            else None,
        )


class TodoCreateSchema(BaseModel):
    """TodoCreateSchema represents data structure as a create model."""

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


class TodoUpdateSchema(BaseModel):
    """TodoUpdateScheme represents data structure as an update model."""

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
