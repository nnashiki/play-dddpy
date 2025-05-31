"""Central exception handlers for FastAPI application."""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
    HTTP_500_INTERNAL_SERVER_ERROR,
)

from dddpy.domain.project.exceptions.duplicate_todo_title_error import (
    DuplicateTodoTitleError,
)
from dddpy.domain.project.exceptions.project_deletion_not_allowed_error import (
    ProjectDeletionNotAllowedError,
)
from dddpy.domain.project.exceptions.project_not_found_error import ProjectNotFoundError
from dddpy.domain.project.exceptions.todo_removal_not_allowed_error import (
    TodoRemovalNotAllowedError,
)
from dddpy.domain.project.exceptions.too_many_todos_error import TooManyTodosError
from dddpy.domain.todo.exceptions.self_dependency_error import SelfDependencyError
from dddpy.domain.todo.exceptions.todo_already_completed_error import (
    TodoAlreadyCompletedError,
)
from dddpy.domain.todo.exceptions.todo_already_started_error import (
    TodoAlreadyStartedError,
)
from dddpy.domain.todo.exceptions.todo_circular_dependency_error import (
    TodoCircularDependencyError,
)
from dddpy.domain.todo.exceptions.todo_dependency_not_completed_error import (
    TodoDependencyNotCompletedError,
)
from dddpy.domain.todo.exceptions.todo_dependency_not_found_error import (
    TodoDependencyNotFoundError,
)
from dddpy.domain.todo.exceptions.todo_not_found_error import TodoNotFoundError
from dddpy.domain.todo.exceptions.todo_not_started_error import TodoNotStartedError
from dddpy.domain.todo.exceptions.too_many_dependencies_error import (
    TooManyDependenciesError,
)


def _create_error_response(
    status_code: int, message: str, error_type: str | None = None
) -> JSONResponse:
    """Create standardized error response."""
    content = {
        'detail': message,
        'error_type': error_type,
    }
    return JSONResponse(status_code=status_code, content=content)


def add_exception_handlers(app):
    """Add centralized exception handlers to the FastAPI application."""

    @app.exception_handler(ProjectNotFoundError)
    async def handle_project_not_found(request: Request, exc: ProjectNotFoundError):
        return _create_error_response(
            HTTP_404_NOT_FOUND, str(exc), 'ProjectNotFoundError'
        )

    @app.exception_handler(TodoNotFoundError)
    async def handle_todo_not_found(request: Request, exc: TodoNotFoundError):
        return _create_error_response(HTTP_404_NOT_FOUND, str(exc), 'TodoNotFoundError')

    @app.exception_handler(ProjectDeletionNotAllowedError)
    async def handle_project_delete_blocked(
        request: Request, exc: ProjectDeletionNotAllowedError
    ):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TodoRemovalNotAllowedError)
    async def handle_todo_removal_blocked(
        request: Request, exc: TodoRemovalNotAllowedError
    ):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TodoDependencyNotFoundError)
    async def handle_dep_not_found(request: Request, exc: TodoDependencyNotFoundError):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TodoDependencyNotCompletedError)
    async def handle_dep_not_complete(
        request: Request, exc: TodoDependencyNotCompletedError
    ):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TodoAlreadyStartedError)
    async def handle_already_started(request: Request, exc: TodoAlreadyStartedError):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TodoAlreadyCompletedError)
    async def handle_already_completed(
        request: Request, exc: TodoAlreadyCompletedError
    ):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TodoCircularDependencyError)
    async def handle_circular_dep(request: Request, exc: TodoCircularDependencyError):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TodoNotStartedError)
    async def handle_todo_not_started(request: Request, exc: TodoNotStartedError):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(DuplicateTodoTitleError)
    async def handle_duplicate_todo_title(
        request: Request, exc: DuplicateTodoTitleError
    ):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TooManyTodosError)
    async def handle_too_many_todos(request: Request, exc: TooManyTodosError):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(SelfDependencyError)
    async def handle_self_dependency(request: Request, exc: SelfDependencyError):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(TooManyDependenciesError)
    async def handle_too_many_dependencies(
        request: Request, exc: TooManyDependenciesError
    ):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(ValueError)
    async def handle_value_error(request: Request, exc: ValueError):
        return JSONResponse(
            status_code=HTTP_400_BAD_REQUEST, content={'detail': str(exc)}
        )

    @app.exception_handler(Exception)
    async def handle_general_exception(request: Request, exc: Exception):
        return JSONResponse(
            status_code=HTTP_500_INTERNAL_SERVER_ERROR,
            content={'detail': 'Internal server error'},
        )
