"""This module provides use case for finding all Project entities."""

from abc import ABC, abstractmethod
from typing import List

from dddpy.dto.project import ProjectOutputDto
from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository


class FindProjectsUseCase(ABC):
    """FindProjectsUseCase defines a use case interface for finding all Projects."""

    @abstractmethod
    def execute(self) -> List[ProjectOutputDto]:
        """execute finds all Projects."""


class FindProjectsUseCaseImpl(FindProjectsUseCase):
    """FindProjectsUseCaseImpl implements the use case for finding all Projects."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self) -> List[ProjectOutputDto]:
        """execute finds all Projects."""
        projects = self.project_repository.find_all()

        # Convert to output DTOs
        return [
            ProjectOutputDto(
                id=str(project.id.value),
                name=project.name.value,
                description=project.description.value,
                todos=[
                    TodoOutputDto(
                        id=str(todo.id.value),
                        title=todo.title.value,
                        description=todo.description.value if todo.description else None,
                        status=todo.status.value,
                        dependencies=[str(dep_id.value) for dep_id in todo.dependencies.values],
                        created_at=todo.created_at,
                        updated_at=todo.updated_at,
                        completed_at=todo.completed_at,
                    )
                    for todo in project.todos
                ],
                created_at=project.created_at,
                updated_at=project.updated_at,
            )
            for project in projects
        ]


def new_find_projects_usecase(project_repository: ProjectRepository) -> FindProjectsUseCase:
    """Create a new instance of FindProjectsUseCase."""
    return FindProjectsUseCaseImpl(project_repository)
