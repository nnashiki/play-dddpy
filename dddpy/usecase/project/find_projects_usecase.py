"""UoW-based FindProjectsUseCase implementation."""

from abc import ABC, abstractmethod

from dddpy.dto.project import ProjectOutputDto
from dddpy.usecase.converter.todo_converter import TodoConverter
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.infrastructure.sqlite.project.project_repository import (
    new_project_repository,
)


class FindProjectsUseCase(ABC):
    """FindProjectsUseCase defines a use case interface for finding all Projects."""

    @abstractmethod
    def execute(self) -> list[ProjectOutputDto]:
        """execute finds all Projects."""


class FindProjectsUseCaseImpl(FindProjectsUseCase):
    """UoW-based implementation of FindProjectsUseCase."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(self) -> list[ProjectOutputDto]:
        """execute finds all Projects with UoW support."""
        result: list[ProjectOutputDto]

        with self.uow as uow:
            # Check that UoW was properly initialized
            if uow.session is None:
                raise RuntimeError('UoW was not properly initialized')

            # Create repository with UoW session
            project_repository = new_project_repository(uow.session)

            # Find all projects
            projects = project_repository.find_all()

            # Convert to output DTOs
            result = [
                ProjectOutputDto(
                    id=str(project.id.value),
                    name=project.name.value,
                    description=project.description.value,
                    todos=[TodoConverter.to_output_dto(todo) for todo in project.todos],
                    created_at=project.created_at,
                    updated_at=project.updated_at,
                )
                for project in projects
            ]

        return result


def new_find_projects_usecase(
    uow: SqlAlchemyUnitOfWork,
) -> FindProjectsUseCase:
    """Create a new instance of FindProjectsUseCase."""
    return FindProjectsUseCaseImpl(uow)
