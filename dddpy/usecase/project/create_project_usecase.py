"""This module provides use case for creating a new Project entity."""

from abc import ABC, abstractmethod

from dddpy.domain.project.entities import Project
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.services import ProjectDomainService
from dddpy.domain.project.value_objects import ProjectName
from dddpy.dto.project import ProjectCreateDto, ProjectOutputDto


class CreateProjectUseCase(ABC):
    """CreateProjectUseCase defines a use case interface for creating a new Project."""

    @abstractmethod
    def execute(self, dto: ProjectCreateDto) -> ProjectOutputDto:
        """execute creates a new Project."""


class CreateProjectUseCaseImpl(CreateProjectUseCase):
    """CreateProjectUseCaseImpl implements the use case for creating a new Project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, dto: ProjectCreateDto) -> ProjectOutputDto:
        """execute creates a new Project."""
        # Validate project name uniqueness using domain service
        name_vo = ProjectName(dto.name)
        if not ProjectDomainService.is_project_name_unique(
            name_vo, self.project_repository
        ):
            raise ValueError(f"Project name '{dto.name}' already exists")

        # Create project
        project = Project.create(dto.name, dto.description)

        # Save project
        self.project_repository.save(project)

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
) -> CreateProjectUseCase:
    """Create a new instance of CreateProjectUseCase."""
    return CreateProjectUseCaseImpl(project_repository)
