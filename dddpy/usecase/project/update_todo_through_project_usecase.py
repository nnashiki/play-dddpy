"""This module provides use case for updating a Todo through Project aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.dto.todo import TodoUpdateDto, TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.todo.value_objects import (
    TodoId,
    TodoTitle,
    TodoDescription,
)


class UpdateTodoThroughProjectUseCase(ABC):
    """UpdateTodoThroughProjectUseCase defines an interface for updating a Todo through Project."""

    @abstractmethod
    def execute(self, todo_id: str, dto: TodoUpdateDto) -> TodoOutputDto:
        """execute updates a Todo through Project aggregate."""


class UpdateTodoThroughProjectUseCaseImpl(UpdateTodoThroughProjectUseCase):
    """UpdateTodoThroughProjectUseCaseImpl implements the use case for updating a Todo through Project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, todo_id: str, dto: TodoUpdateDto) -> TodoOutputDto:
        """execute updates a Todo through Project aggregate."""
        _todo_id = TodoId(UUID(todo_id))
        
        # Find the project that contains this todo
        project = self.project_repository.find_project_by_todo_id(_todo_id)
        
        if project is None:
            raise ProjectNotFoundError()
        
        # Convert DTO to domain objects
        title = TodoTitle(dto.title) if dto.title is not None else None
        description = TodoDescription(dto.description) if dto.description is not None else None
        dependencies = [TodoId(UUID(dep_id)) for dep_id in dto.dependencies] if dto.dependencies is not None else None
        
        # Update todo through project
        updated_todo = project.update_todo_by_id(_todo_id, title, description, dependencies)
        
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


def new_update_todo_through_project_usecase(project_repository: ProjectRepository) -> UpdateTodoThroughProjectUseCase:
    """Create a new instance of UpdateTodoThroughProjectUseCase."""
    return UpdateTodoThroughProjectUseCaseImpl(project_repository)
