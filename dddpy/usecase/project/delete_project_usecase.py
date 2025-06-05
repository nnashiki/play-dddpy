"""UoW-based DeleteProjectUseCase implementation."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.exceptions import (
    ProjectDeletionNotAllowedError,
    ProjectNotFoundError,
)
from dddpy.domain.project.services import ProjectDomainService
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.project.events import ProjectDeletedEvent
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.project.project_repository import (
    new_project_repository,
)


class DeleteProjectUseCase(ABC):
    """Abstract base class for delete project use case."""

    @abstractmethod
    def execute(self, project_id: str) -> None:
        """Execute the delete project use case."""
        ...


class DeleteProjectUseCaseImpl(DeleteProjectUseCase):
    """UoW-based implementation of delete project use case."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(self, project_id: str) -> None:
        """Execute the delete project use case with transactional outbox support."""
        with self.uow as uow:
            # Check that UoW was properly initialized
            if uow.session is None or uow.event_publisher is None:
                raise RuntimeError('UoW was not properly initialized')

            # Create repository with UoW session
            project_repository = new_project_repository(uow.session)

            # Convert to value object
            _id = ProjectId(UUID(project_id))
            
            # Find project (need info for event before deletion)
            project = project_repository.find_by_id(_id)
            if project is None:
                raise ProjectNotFoundError()

            # Check if project can be deleted using domain service
            if not ProjectDomainService.can_delete_project(project):
                raise ProjectDeletionNotAllowedError()

            # Create and publish deletion event before actual deletion
            event = ProjectDeletedEvent(
                project_id=project.id.value,
                name=project.name.value,
                description=project.description.value if project.description.value else None,
                occurred_at=None,  # Will be set by DomainEvent base class
            )
            uow.event_publisher.publish(event)

            # Perform the actual deletion
            project_repository.delete(_id)

            # UoW will flush events to outbox and commit transaction


def new_delete_project_usecase(
    uow: SqlAlchemyUnitOfWork,
) -> DeleteProjectUseCase:
    """Factory function for creating DeleteProjectUseCase."""
    return DeleteProjectUseCaseImpl(uow)
