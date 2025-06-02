"""This module provides use case for creating a new Project entity."""

from abc import ABC, abstractmethod

from dddpy.domain.project.entities import Project
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.services import ProjectDomainService
from dddpy.domain.project.value_objects import ProjectName
from dddpy.domain.project.events.project_created_event import ProjectCreatedEvent
from dddpy.domain.todo.events import TodoCreatedEvent
from dddpy.domain.shared.events import DomainEventPublisher
from dddpy.dto.project import ProjectCreateDto, ProjectOutputDto
from dddpy.usecase.assembler.project_create_assembler import ProjectCreateAssembler
from dddpy.infrastructure.handlers.project_history_handler import on_project_created
from dddpy.infrastructure.handlers.todo_history_handler import on_todo_created


class CreateProjectUseCase(ABC):
    """CreateProjectUseCase defines a use case interface for creating a new Project."""

    @abstractmethod
    def execute(self, dto: ProjectCreateDto) -> ProjectOutputDto:
        """execute creates a new Project."""


class CreateProjectUseCaseImpl(CreateProjectUseCase):
    """CreateProjectUseCaseImpl implements the use case for creating a new Project."""

    def __init__(
        self,
        project_repository: ProjectRepository,
        event_publisher: DomainEventPublisher,
    ):
        self.project_repository = project_repository
        self.event_publisher = event_publisher

    def execute(self, dto: ProjectCreateDto) -> ProjectOutputDto:
        """execute creates a new Project."""
        # Validate project name uniqueness using domain service
        name_vo = ProjectName(dto.name)
        if not ProjectDomainService.is_project_name_unique(
            name_vo, self.project_repository
        ):
            raise ValueError(f"Project name '{dto.name}' already exists")

        # Create project using Assembler with event publisher
        project = ProjectCreateAssembler.to_entity(dto, self.event_publisher)

        # Save project
        self.project_repository.save(project)

        # Handle events (履歴保存など) - 同一トランザクション内で直接実行
        if project.has_events():
            session = self.project_repository.get_session()

            # シンプルに直接ハンドラーを呼び出し（同一トランザクション）
            for event in project.get_events():
                if event.event_type == 'ProjectCreated' and isinstance(event, ProjectCreatedEvent):
                    on_project_created(event, session)
                elif event.event_type == 'TodoCreated' and isinstance(event, TodoCreatedEvent):
                    on_todo_created(event, session)

        # Convert to output DTO
        return ProjectOutputDto(
            id=str(project.id.value),
            name=project.name.value,
            description=project.description.value,
            todos=[],  # New project has no todos
            created_at=project.created_at,
            updated_at=project.updated_at,
        )


def new_create_project_usecase(
    project_repository: ProjectRepository,
    event_publisher: DomainEventPublisher,
) -> CreateProjectUseCase:
    """Create a new instance of CreateProjectUseCase."""
    return CreateProjectUseCaseImpl(project_repository, event_publisher)
