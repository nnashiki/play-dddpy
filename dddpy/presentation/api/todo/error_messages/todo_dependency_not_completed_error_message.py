"""Error message for TodoDependencyNotCompletedError."""

from pydantic import BaseModel


class TodoDependencyNotCompletedErrorMessage(BaseModel):
    """Error message for TodoDependencyNotCompletedError."""

    error_type: str = 'todo_dependency_not_completed_error'
    message: str = 'Cannot start todo because dependencies are not completed'
