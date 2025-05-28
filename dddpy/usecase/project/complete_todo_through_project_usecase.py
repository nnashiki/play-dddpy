"""This module provides use case for completing a Todo through Project aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.todo.value_objects import TodoId


class CompleteTodoThroughProjectUseCase(ABC):
    """CompleteTodoThroughProjectUseCase defines an interface for completing a Todo through Project."""

    @abstractmethod
    def execute(self, todo_id: str) -> TodoOutputDto:
        """execute completes a Todo through Project aggregate."""


class CompleteTodoThroughProjectUseCaseImpl(CompleteTodoThroughProjectUseCase):
    """CompleteTodoThroughProjectUseCaseImpl implements the use case for completing a Todo through Project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, todo_id: str) -> TodoOutputDto:
        """execute completes a Todo through Project aggregate."""
        _todo_id = TodoId(UUID(todo_id))
        
        # Find the project that contains this todo
        project = self.project_repository.find_project_by_todo_id(_todo_id)
        
        if project is None:
            raise ProjectNotFoundError()
        
        # Complete todo through project
        updated_todo = project.complete_todo_by_id(_todo_id)
        
        # Save project with updated todo
        self.project_repository.save(project)

        # Convert to output DTO
        return TodoOutputDto(
            id=str(updated_todo.id.value),
            title=updated_todo.title.value,
            description=updated_todo.description.value if updated_todo.description else None,
            status=updated_todo.status.value,
            dependencies=[str(dep_id.value) for dep_id in updated_todo.dependencies.values],
            created_at=updated_todo.created_at,
            updated_at=updated_todo.updated_at,
            completed_at=updated_todo.completed_at,
        )


def new_complete_todo_through_project_usecase(project_repository: ProjectRepository) -> CompleteTodoThroughProjectUseCase:
    """Create a new instance of CompleteTodoThroughProjectUseCase."""
    return CompleteTodoThroughProjectUseCaseImpl(project_repository)
