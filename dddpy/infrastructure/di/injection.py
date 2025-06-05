"""Dependency-injection configuration for the application."""

from collections.abc import Iterator

from fastapi import Depends

from dddpy.domain.shared.events import get_event_publisher, DomainEventPublisher
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.usecase.project import (
    CompleteTodoThroughProjectUseCase,
    # Project-level use-cases
    CreateProjectUseCase,
    FindProjectsUseCase,
    StartTodoThroughProjectUseCase,
    UpdateTodoThroughProjectUseCase,
    new_complete_todo_through_project_usecase,
    new_create_project_usecase,
    new_find_projects_usecase,
    new_start_todo_through_project_usecase,
    new_update_todo_through_project_usecase,
)
from dddpy.usecase.project.add_todo_to_project_usecase import (
    AddTodoToProjectUseCase,
    new_add_todo_to_project_usecase,
)
from dddpy.usecase.project.delete_project_usecase import (
    DeleteProjectUseCase,
    new_delete_project_usecase,
)
from dddpy.usecase.todo.find_todo_usecase import (
    FindTodoThroughProjectUseCase,
    new_find_todo_usecase,
)


def get_uow() -> Iterator[SqlAlchemyUnitOfWork]:
    """Provide a Unit of Work with transactional outbox support."""
    with SqlAlchemyUnitOfWork() as uow:
        yield uow


def get_event_publisher_di() -> DomainEventPublisher:
    """Get event publisher from DI container."""
    return get_event_publisher()


def get_create_project_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> CreateProjectUseCase:
    """Get CreateProjectUseCase with Unit of Work support."""
    return new_create_project_usecase(uow)


def get_add_todo_to_project_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> AddTodoToProjectUseCase:
    """Get AddTodoToProjectUseCase with Unit of Work support."""
    return new_add_todo_to_project_usecase(uow)


def get_find_projects_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> FindProjectsUseCase:
    return new_find_projects_usecase(uow)


def get_start_todo_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> StartTodoThroughProjectUseCase:
    return new_start_todo_through_project_usecase(uow)


def get_complete_todo_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> CompleteTodoThroughProjectUseCase:
    return new_complete_todo_through_project_usecase(uow)


def get_update_todo_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> UpdateTodoThroughProjectUseCase:
    return new_update_todo_through_project_usecase(uow)


def get_delete_project_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> DeleteProjectUseCase:
    return new_delete_project_usecase(uow)


def get_find_todo_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> FindTodoThroughProjectUseCase:
    return new_find_todo_usecase(uow)
