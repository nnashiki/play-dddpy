"""Event-aware AddTodoToProjectUseCase with domain event publishing."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.shared.events import get_event_publisher
from dddpy.dto.project import AddTodoToProjectDto
from dddpy.dto.todo import TodoOutputDto
from dddpy.usecase.converter.todo_converter import TodoConverter
from dddpy.usecase.assembler.event_aware_todo_create_assembler import (
    EventAwareTodoCreateAssembler,
)


class EventAwareAddTodoToProjectUseCase(ABC):
    """Event-aware AddTodoToProjectUseCase with domain event publishing."""

    @abstractmethod
    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project with event publishing."""


class EventAwareAddTodoToProjectUseCaseImpl(EventAwareAddTodoToProjectUseCase):
    """Event-aware implementation with full domain event support."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project with full event publishing."""
        _project_id = ProjectId(UUID(project_id))
        project = self.project_repository.find_by_id(_project_id)

        if project is None:
            raise ProjectNotFoundError()

        # Clear previous events for clean state
        event_publisher = get_event_publisher()
        event_publisher.clear_events()

        todo_entity = EventAwareTodoCreateAssembler.to_entity(dto, project_id)

        # Projectに追加（TodoAddedToProjectイベント発行）
        project.add_todo_entity(todo_entity)

        # Save project with new todo
        self.project_repository.save(project)

        # Log events for debugging/monitoring (optional)
        events = event_publisher.get_events()
        print(f'Published {len(events)} domain events:')
        for event in events:
            print(f'  - {event.event_type}: {event.to_dict()}')

        # Convert to output DTO
        return TodoConverter.to_output_dto(todo_entity)


def new_event_aware_add_todo_to_project_usecase(
    project_repository: ProjectRepository,
) -> EventAwareAddTodoToProjectUseCase:
    """Create a new instance of EventAwareAddTodoToProjectUseCase."""
    return EventAwareAddTodoToProjectUseCaseImpl(project_repository)
