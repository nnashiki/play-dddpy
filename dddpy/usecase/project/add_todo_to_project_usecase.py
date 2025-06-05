"""UoW-based AddTodoToProjectUseCase implementation."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.value_objects import ProjectId
from dddpy.dto.project import AddTodoToProjectDto
from dddpy.dto.todo import TodoOutputDto
from dddpy.usecase.converter.todo_converter import TodoConverter
from dddpy.usecase.assembler.todo_create_assembler import TodoCreateAssembler
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.project.project_repository import (
    new_project_repository,
)


class AddTodoToProjectUseCase(ABC):
    """AddTodoToProjectUseCase defines an interface for adding a Todo to a Project."""

    @abstractmethod
    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project."""


class AddTodoToProjectUseCaseImpl(AddTodoToProjectUseCase):
    """UoW-based implementation of AddTodoToProjectUseCase."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project with transactional outbox support."""
        result: TodoOutputDto

        with self.uow as uow:
            # Check that UoW was properly initialized
            if uow.session is None or uow.event_publisher is None:
                raise RuntimeError('UoW was not properly initialized')

            # Create repository with UoW session
            project_repository = new_project_repository(uow.session)

            # Find project
            _project_id = ProjectId(UUID(project_id))
            project = project_repository.find_by_id(_project_id)

            if project is None:
                raise ProjectNotFoundError()

            # Set event publisher for the project
            project.set_event_publisher(uow.event_publisher)

            # Create todo with event publisher support
            todo_entity = TodoCreateAssembler.to_entity(
                dto, project_id, uow.event_publisher
            )

            # Add todo to project
            project.add_todo_entity(todo_entity)

            # Save project with new todo
            project_repository.save(project)

            # Events are automatically published via DomainEventPublisher during todo creation
            # UoW will flush events to outbox and commit transaction

            # Convert to output DTO using Converter (Application 層)
            result = TodoConverter.to_output_dto(todo_entity)

        return result


def new_add_todo_to_project_usecase(
    uow: SqlAlchemyUnitOfWork,
) -> AddTodoToProjectUseCase:
    """Create a new instance of AddTodoToProjectUseCase."""
    return AddTodoToProjectUseCaseImpl(uow)
