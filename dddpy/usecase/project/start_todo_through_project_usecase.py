"""This module provides use case for starting a Todo through Project aggregate."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.exceptions import ProjectNotFoundError
from dddpy.domain.todo.value_objects import TodoId


class StartTodoThroughProjectUseCase(ABC):
    """StartTodoThroughProjectUseCase defines an interface for starting a Todo through Project."""

    @abstractmethod
    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """execute starts a Todo through Project aggregate."""


class StartTodoThroughProjectUseCaseImpl(StartTodoThroughProjectUseCase):
    """StartTodoThroughProjectUseCaseImpl implements the use case for starting a Todo through Project."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """execute starts a Todo through Project aggregate."""
        from dddpy.domain.project.value_objects import ProjectId
        
        _project_id = ProjectId(UUID(project_id))
        _todo_id = TodoId(UUID(todo_id))
        
        # Find the project by ID
        project = self.project_repository.find_by_id(_project_id)
        
        if project is None:
            raise ProjectNotFoundError()
        
        # Start todo through project
        updated_todo = project.start_todo_by_id(_todo_id)
        
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


def new_start_todo_through_project_usecase(project_repository: ProjectRepository) -> StartTodoThroughProjectUseCase:
    """Create a new instance of StartTodoThroughProjectUseCase."""
    return StartTodoThroughProjectUseCaseImpl(project_repository)
