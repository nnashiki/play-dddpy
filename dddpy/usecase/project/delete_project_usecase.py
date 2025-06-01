"""Use case for deleting a project."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import (
    ProjectDeletionNotAllowedError,
    ProjectNotFoundError,
)
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.services import ProjectDomainService
from dddpy.domain.project.value_objects import ProjectId


class DeleteProjectUseCase(ABC):
    """Abstract base class for delete project use case."""

    @abstractmethod
    def execute(self, project_id: str) -> None:
        """Execute the delete project use case."""
        ...


class DeleteProjectUseCaseImpl(DeleteProjectUseCase):
    """Implementation of delete project use case."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str) -> None:
        """Execute the delete project use case."""
        _id = ProjectId(UUID(project_id))
        project = self.project_repository.find_by_id(_id)
        if project is None:
            raise ProjectNotFoundError()

        if not ProjectDomainService.can_delete_project(project):
            raise ProjectDeletionNotAllowedError()

        self.project_repository.delete(_id)


def new_delete_project_usecase(repo: ProjectRepository) -> DeleteProjectUseCase:
    """Factory function for creating DeleteProjectUseCase."""
    return DeleteProjectUseCaseImpl(repo)
