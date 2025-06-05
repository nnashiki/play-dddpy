"""UoW-based CompleteTodoThroughProjectUseCase implementation."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.value_objects import TodoId
from dddpy.dto.todo import TodoOutputDto
from dddpy.usecase.converter.todo_converter import TodoConverter
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.project.project_repository import (
    new_project_repository,
)


class CompleteTodoThroughProjectUseCase(ABC):
    """CompleteTodoThroughProjectUseCase defines an interface for completing a Todo through Project."""

    @abstractmethod
    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """execute completes a Todo through Project aggregate."""


class CompleteTodoThroughProjectUseCaseImpl(CompleteTodoThroughProjectUseCase):
    """UoW-based implementation of CompleteTodoThroughProjectUseCase."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """execute completes a Todo through Project aggregate with transactional outbox support."""
        result: TodoOutputDto

        with self.uow as uow:
            # Check that UoW was properly initialized
            if uow.session is None or uow.event_publisher is None:
                raise RuntimeError('UoW was not properly initialized')

            # Create repository with UoW session
            project_repository = new_project_repository(uow.session)

            # Convert to value objects
            _project_id = ProjectId(UUID(project_id))
            _todo_id = TodoId(UUID(todo_id))

            # Find the project by ID
            project = project_repository.find_by_id(_project_id)
            if project is None:
                raise ProjectNotFoundError()

            # Set event publisher for the project
            project.set_event_publisher(uow.event_publisher)

            # Complete todo through project (this will publish TodoCompleted event)
            updated_todo = project.complete_todo_by_id(_todo_id)

            # Save project with updated todo
            project_repository.save(project)

            # Convert to output DTO using Converter (Application 層)
            result = TodoConverter.to_output_dto(updated_todo)

            # UoW will flush events to outbox and commit transaction

        return result


def new_complete_todo_through_project_usecase(
    uow: SqlAlchemyUnitOfWork,
) -> CompleteTodoThroughProjectUseCase:
    """Create a new instance of CompleteTodoThroughProjectUseCase."""
    return CompleteTodoThroughProjectUseCaseImpl(uow)
