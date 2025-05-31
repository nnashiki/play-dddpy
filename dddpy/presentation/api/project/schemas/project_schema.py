"""Query model for Project entities in the application."""

from pydantic import BaseModel, Field

from dddpy.presentation.api.project.schemas.project_todo_schema import ProjectTodoSchema


class ProjectSchema(BaseModel):
    """ProjectSchema represents data structure as a read model."""

    id: str = Field(examples=['123e4567-e89b-12d3-a456-426614174000'])
    name: str = Field(examples=['My Project'])
    description: str = Field(examples=['A sample project for demonstration'])
    todos: list[ProjectTodoSchema] = Field(examples=[[]])
    created_at: int = Field(examples=[1136214245000])
    updated_at: int = Field(examples=[1136214245000])

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True


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
    dependencies: list[str] | None = Field(
        default=None,
        examples=[['456e4567-e89b-12d3-a456-426614174001']],
        description='List of Todo IDs that this Todo depends on',
    )
