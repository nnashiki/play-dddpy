"""This module provides use case for adding a Todo to a Project."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.shared.events import DomainEventPublisher
from dddpy.dto.project import AddTodoToProjectDto
from dddpy.dto.todo import TodoOutputDto
from dddpy.usecase.converter.todo_converter import TodoConverter
from dddpy.usecase.assembler.todo_create_assembler import TodoCreateAssembler


class AddTodoToProjectUseCase(ABC):
    """AddTodoToProjectUseCase defines an interface for adding a Todo to a Project."""

    @abstractmethod
    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project."""


class AddTodoToProjectUseCaseImpl(AddTodoToProjectUseCase):
    """AddTodoToProjectUseCaseImpl implements the use case for adding a Todo to a Project."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        event_publisher: DomainEventPublisher,
    ):
        self.project_repository = project_repository
        self.event_publisher = event_publisher

    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project."""
        _project_id = ProjectId(UUID(project_id))
        project = self.project_repository.find_by_id(_project_id)

        if project is None:
            raise ProjectNotFoundError()

        # Set event publisher for the project
        project.set_event_publisher(self.event_publisher)

        # Set database session for event handlers
        session = self.project_repository.get_session()
        self.event_publisher.set_session(session)

        # Create todo with event publisher support
        todo_entity = TodoCreateAssembler.to_entity(
            dto, project_id, self.event_publisher
        )
        # Note: Todo creation events will be handled when the todo is created

        project.add_todo_entity(todo_entity)

        # Save project with new todo
        self.project_repository.save(project)

        # Convert to output DTO using Converter (Application 層)
        return TodoConverter.to_output_dto(todo_entity)


def new_add_todo_to_project_usecase(
    project_repository: ProjectRepository,
    event_publisher: DomainEventPublisher,
) -> AddTodoToProjectUseCase:
    """Create a new instance of AddTodoToProjectUseCase."""
    return AddTodoToProjectUseCaseImpl(project_repository, event_publisher)
