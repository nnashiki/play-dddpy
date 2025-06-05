"""UoW-based UpdateTodoThroughProjectUseCase implementation."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.value_objects import (
    TodoDescription,
    TodoId,
    TodoTitle,
)
from dddpy.dto.todo import TodoOutputDto, TodoUpdateDto
from dddpy.usecase.converter.todo_converter import TodoConverter
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.project.project_repository import (
    new_project_repository,
)


class UpdateTodoThroughProjectUseCase(ABC):
    """UpdateTodoThroughProjectUseCase defines an interface for updating a Todo through Project."""

    @abstractmethod
    def execute(
        self, project_id: str, todo_id: str, dto: TodoUpdateDto
    ) -> TodoOutputDto:
        """execute updates a Todo through Project aggregate."""


class UpdateTodoThroughProjectUseCaseImpl(UpdateTodoThroughProjectUseCase):
    """UoW-based implementation of UpdateTodoThroughProjectUseCase."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(
        self, project_id: str, todo_id: str, dto: TodoUpdateDto
    ) -> TodoOutputDto:
        """execute updates a Todo through Project aggregate with transactional outbox support."""
        result: TodoOutputDto

        with self.uow as uow:
            # Check that UoW was properly initialized
            if uow.session is None or uow.event_publisher is None:
                raise RuntimeError('UoW was not properly initialized')

            # Create repository with UoW session
            project_repository = new_project_repository(uow.session)

            _project_id = ProjectId(UUID(project_id))
            _todo_id = TodoId(UUID(todo_id))

            # Find the project by ID
            project = project_repository.find_by_id(_project_id)

            if project is None:
                raise ProjectNotFoundError()

            # Set event publisher for the project
            project.set_event_publisher(uow.event_publisher)

            # Convert DTO to domain objects
            title = TodoTitle(dto.title) if dto.title is not None else None
            description = (
                TodoDescription(dto.description) if dto.description is not None else None
            )
            dependencies = (
                [TodoId(UUID(dep_id)) for dep_id in dto.dependencies]
                if dto.dependencies is not None
                else None
            )

            # Update todo through project
            updated_todo = project.update_todo_by_id(
                _todo_id, title, description, dependencies
            )

            # Save project with updated todo
            project_repository.save(project)

            # Events are automatically published via DomainEventPublisher during todo update
            # UoW will flush events to outbox and commit transaction

            # Convert to output DTO using Converter (Application 層)
            result = TodoConverter.to_output_dto(updated_todo)

        return result


def new_update_todo_through_project_usecase(
    uow: SqlAlchemyUnitOfWork,
) -> UpdateTodoThroughProjectUseCase:
    """Create a new instance of UpdateTodoThroughProjectUseCase."""
    return UpdateTodoThroughProjectUseCaseImpl(uow)
