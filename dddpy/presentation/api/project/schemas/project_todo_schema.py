"""Todo schemas for Project API endpoints."""


from pydantic import BaseModel, Field


class ProjectTodoSchema(BaseModel):
    """ProjectTodoSchema represents Todo data structure in Project context."""

    id: str = Field(examples=['123e4567-e89b-12d3-a456-426614174000'])
    title: str = Field(examples=['Complete the project'])
    description: str = Field(examples=['Finish implementing the DDD architecture'])
    status: str = Field(examples=['not_started'])
    dependencies: list[str] = Field(examples=[['456e4567-e89b-12d3-a456-426614174001']])
    project_id: str = Field(
        examples=['789e4567-e89b-12d3-a456-426614174002']
    )  # Added for clarity
    created_at: int = Field(examples=[1136214245000])
    updated_at: int = Field(examples=[1136214245000])
    completed_at: int | None = Field(examples=[1136214245000])

    class Config:
        """Configuration for Pydantic model."""

        from_attributes = True


class ProjectTodoUpdateSchema(BaseModel):
    """ProjectTodoUpdateSchema represents data structure for updating Todo in Project context."""

    title: str = Field(min_length=1, max_length=100, examples=['Complete the project'])
    description: str | None = Field(
        default=None,
        max_length=1000,
        examples=['Finish implementing the DDD architecture'],
    )
    dependencies: list[str] | None = Field(
        default=None,
        examples=[['456e4567-e89b-12d3-a456-426614174001']],
        description='List of Todo IDs that this Todo depends on',
    )
