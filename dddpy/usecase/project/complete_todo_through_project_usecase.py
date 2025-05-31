"""This module provides use case for completing a Todo through Project aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.todo.value_objects import TodoId
from dddpy.presentation.assembler import ProjectTodoAssembler


class CompleteTodoThroughProjectUseCase(ABC):
    """CompleteTodoThroughProjectUseCase defines an interface for completing a Todo through Project."""

    @abstractmethod
    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """execute completes a Todo through Project aggregate."""


class CompleteTodoThroughProjectUseCaseImpl(CompleteTodoThroughProjectUseCase):
    """CompleteTodoThroughProjectUseCaseImpl implements the use case for completing a Todo through Project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """execute completes a Todo through Project aggregate."""
        from dddpy.domain.project.value_objects import ProjectId

        _project_id = ProjectId(UUID(project_id))
        _todo_id = TodoId(UUID(todo_id))

        # Find the project by ID
        project = self.project_repository.find_by_id(_project_id)

        if project is None:
            raise ProjectNotFoundError()

        # Complete todo through project
        updated_todo = project.complete_todo_by_id(_todo_id)

        # Save project with updated todo
        self.project_repository.save(project)

        # Convert to output DTO using Assembler
        return ProjectTodoAssembler.to_output_dto(updated_todo)


def new_complete_todo_through_project_usecase(
    project_repository: ProjectRepository,
) -> CompleteTodoThroughProjectUseCase:
    """Create a new instance of CompleteTodoThroughProjectUseCase."""
    return CompleteTodoThroughProjectUseCaseImpl(project_repository)
