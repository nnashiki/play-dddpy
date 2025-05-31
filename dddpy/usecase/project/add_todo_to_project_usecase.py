"""This module provides use case for adding a Todo to a Project."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.dto.project import AddTodoToProjectDto
from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.todo.value_objects import (
    TodoDescription,
    TodoId,
    TodoTitle,
)
from dddpy.presentation.assembler import ProjectTodoAssembler


class AddTodoToProjectUseCase(ABC):
    """AddTodoToProjectUseCase defines an interface for adding a Todo to a Project."""

    @abstractmethod
    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project."""


class AddTodoToProjectUseCaseImpl(AddTodoToProjectUseCase):
    """AddTodoToProjectUseCaseImpl implements the use case for adding a Todo to a Project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        """execute adds a Todo to a Project."""
        _project_id = ProjectId(UUID(project_id))
        project = self.project_repository.find_by_id(_project_id)

        if project is None:
            raise ProjectNotFoundError()

        # Convert DTO to domain objects
        title = TodoTitle(dto.title)
        description = TodoDescription(dto.description) if dto.description else None

        # Convert dependencies
        dependencies = None
        if dto.dependencies:
            dependencies = [TodoId(UUID(dep_id)) for dep_id in dto.dependencies]

        # Add todo to project (with validation)
        todo = project.add_todo(title, description, dependencies)

        # Save project with new todo
        self.project_repository.save(project)

        # Convert to output DTO using Assembler
        return ProjectTodoAssembler.to_output_dto(todo)


def new_add_todo_to_project_usecase(
    project_repository: ProjectRepository,
) -> AddTodoToProjectUseCase:
    """Create a new instance of AddTodoToProjectUseCase."""
    return AddTodoToProjectUseCaseImpl(project_repository)
