"""Create model for Todo entities in the application."""

from typing import List
from pydantic import BaseModel, Field


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
