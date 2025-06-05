"""UoW-based CreateProjectUseCase implementation."""

from abc import ABC, abstractmethod

from dddpy.domain.project.services import ProjectDomainService
from dddpy.domain.project.value_objects import ProjectName
from dddpy.dto.project import ProjectCreateDto, ProjectOutputDto
from dddpy.usecase.assembler.project_create_assembler import ProjectCreateAssembler
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.project.project_repository import (
    new_project_repository,
)


class CreateProjectUseCase(ABC):
    """CreateProjectUseCase defines a use case interface for creating a new Project."""

    @abstractmethod
    def execute(self, dto: ProjectCreateDto) -> ProjectOutputDto:
        """execute creates a new Project."""


class CreateProjectUseCaseImpl(CreateProjectUseCase):
    """UoW-based implementation of CreateProjectUseCase."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(self, dto: ProjectCreateDto) -> ProjectOutputDto:
        """execute creates a new Project with transactional outbox support."""
        result: ProjectOutputDto

        with self.uow as uow:
            # Check that UoW was properly initialized
            if uow.session is None or uow.event_publisher is None:
                raise RuntimeError('UoW was not properly initialized')

            # Create repository with UoW session
            project_repository = new_project_repository(uow.session)

            # Validate project name uniqueness using domain service
            name_vo = ProjectName(dto.name)
            if not ProjectDomainService.is_project_name_unique(
                name_vo, project_repository
            ):
                raise ValueError(f"Project name '{dto.name}' already exists")

            # Create project using Assembler with event publisher from UoW
            project = ProjectCreateAssembler.to_entity(dto, uow.event_publisher)

            # Save project
            project_repository.save(project)

            # Events are automatically published via DomainEventPublisher during project creation
            # UoW will flush events to outbox and commit transaction

            # Convert to output DTO
            result = ProjectOutputDto(
                id=str(project.id.value),
                name=project.name.value,
                description=project.description.value,
                todos=[],  # New project has no todos
                created_at=project.created_at,
                updated_at=project.updated_at,
            )

        return result


def new_create_project_usecase(
    uow: SqlAlchemyUnitOfWork,
) -> CreateProjectUseCase:
    """Create a new instance of CreateProjectUseCase."""
    return CreateProjectUseCaseImpl(uow)
