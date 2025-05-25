"""Error message model for when a dependency Todo is not found."""

from pydantic import BaseModel, Field


class ErrorMessageTodoDependencyNotFound(BaseModel):
    """Error message model for when a dependency Todo is not found."""

    detail: str = Field(examples=['Dependency todo with id {id} not found'])
