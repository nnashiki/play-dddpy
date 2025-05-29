"""Error message schemas for Project Todo API endpoints."""

from pydantic import BaseModel, Field


class ErrorMessageTodoNotFound(BaseModel):
    """Error message for Todo not found."""
    
    detail: str = Field(
        default="Todo not found",
        examples=["Todo not found"]
    )
    error_type: str = Field(
        default="TodoNotFoundError",
        examples=["TodoNotFoundError"]
    )


class TodoDependencyNotCompletedErrorMessage(BaseModel):
    """Error message for Todo dependency not completed."""
    
    detail: str = Field(
        default="Cannot start todo because dependencies are not completed",
        examples=["Cannot start todo because dependencies are not completed"]
    )
    error_type: str = Field(
        default="TodoDependencyNotCompletedError",
        examples=["TodoDependencyNotCompletedError"]
    )
