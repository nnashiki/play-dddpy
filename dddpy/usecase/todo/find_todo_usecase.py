"""Use case for finding a todo through project."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import TodoId
from dddpy.domain.todo.exceptions import TodoNotFoundError


class FindTodoThroughProjectUseCase(ABC):
    """Abstract base class for find todo through project use case."""

    @abstractmethod
    def execute(self, todo_id: str) -> TodoOutputDto:
        """Execute the find todo through project use case."""
        ...


class FindTodoThroughProjectUseCaseImpl(FindTodoThroughProjectUseCase):
    """Implementation of find todo through project use case."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, todo_id: str) -> TodoOutputDto:
        """Execute the find todo through project use case."""
        _todo_id = TodoId(UUID(todo_id))
        project = self.project_repository.find_project_by_todo_id(_todo_id)
        if project is None:
            raise TodoNotFoundError()
        
        todo = project.get_todo(_todo_id)
        return TodoOutputDto(
            id=str(todo.id.value),
            title=todo.title.value,
            description=todo.description.value if todo.description else None,
            status=todo.status.value,
            dependencies=[str(d.value) for d in todo.dependencies.values],
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            completed_at=todo.completed_at,
        )


def new_find_todo_usecase(repo: ProjectRepository) -> FindTodoThroughProjectUseCase:
    """Factory function for creating FindTodoThroughProjectUseCase."""
    return FindTodoThroughProjectUseCaseImpl(repo)
