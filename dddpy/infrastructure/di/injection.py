"""Dependency-injection configuration for the application."""

from collections.abc import Iterator

from fastapi import Depends
from sqlalchemy.orm import Session

from dddpy.domain.project.repositories import ProjectRepository
from dddpy.infrastructure.sqlite.database import SessionLocal
from dddpy.infrastructure.sqlite.project.project_repository import (
    new_project_repository,
)
from dddpy.usecase.project import (
    AddTodoToProjectUseCase,
    CompleteTodoThroughProjectUseCase,
    # Project-level use-cases
    CreateProjectUseCase,
    FindProjectsUseCase,
    StartTodoThroughProjectUseCase,
    UpdateTodoThroughProjectUseCase,
    new_add_todo_to_project_usecase,
    new_complete_todo_through_project_usecase,
    new_create_project_usecase,
    new_find_projects_usecase,
    new_start_todo_through_project_usecase,
    new_update_todo_through_project_usecase,
)
from dddpy.usecase.project.delete_project_usecase import (
    DeleteProjectUseCase,
    new_delete_project_usecase,
)
from dddpy.usecase.todo.find_todo_usecase import (
    FindTodoThroughProjectUseCase,
    new_find_todo_usecase,
)


def get_session() -> Iterator[Session]:
    """Provide a SQLAlchemy session (commit / rollback handled here)."""
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:  # pragma: no cover
        session.rollback()
        raise
    finally:
        session.close()


def get_project_repository(
    session: Session = Depends(get_session),
) -> ProjectRepository:
    """ProjectRepository provider."""
    return new_project_repository(session)


def get_create_project_usecase(
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> CreateProjectUseCase:
    return new_create_project_usecase(project_repository)


def get_add_todo_to_project_usecase(
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> AddTodoToProjectUseCase:
    return new_add_todo_to_project_usecase(project_repository)


def get_find_projects_usecase(
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> FindProjectsUseCase:
    return new_find_projects_usecase(project_repository)


def get_start_todo_usecase(
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> StartTodoThroughProjectUseCase:
    return new_start_todo_through_project_usecase(project_repository)


def get_complete_todo_usecase(
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> CompleteTodoThroughProjectUseCase:
    return new_complete_todo_through_project_usecase(project_repository)


def get_update_todo_usecase(
    project_repository: ProjectRepository = Depends(get_project_repository),
) -> UpdateTodoThroughProjectUseCase:
    return new_update_todo_through_project_usecase(project_repository)


def get_delete_project_usecase(
    repo: ProjectRepository = Depends(get_project_repository),
) -> DeleteProjectUseCase:
    return new_delete_project_usecase(repo)


def get_find_todo_usecase(
    repo: ProjectRepository = Depends(get_project_repository),
) -> FindTodoThroughProjectUseCase:
    return new_find_todo_usecase(repo)
