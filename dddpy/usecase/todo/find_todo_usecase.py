"""Use case for finding a todo through project."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.dto.todo import TodoOutputDto
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import TodoId
from dddpy.domain.todo.exceptions import TodoNotFoundError
from dddpy.presentation.assembler import ProjectTodoAssembler


class FindTodoThroughProjectUseCase(ABC):
    """Abstract base class for find todo through project use case."""

    @abstractmethod
    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """Execute the find todo through project use case."""
        ...


class FindTodoThroughProjectUseCaseImpl(FindTodoThroughProjectUseCase):
    """Implementation of find todo through project use case."""

    def __init__(self, project_repository: ProjectRepository):
        self.project_repository = project_repository

    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """Execute the find todo through project use case."""
        from dddpy.domain.project.value_objects import ProjectId

        _project_id = ProjectId(UUID(project_id))
        _todo_id = TodoId(UUID(todo_id))

        project = self.project_repository.find_by_id(_project_id)
        if project is None:
            from dddpy.domain.project.exceptions import ProjectNotFoundError

            raise ProjectNotFoundError()

        todo = project.get_todo(_todo_id)
        return ProjectTodoAssembler.to_output_dto(todo)


def new_find_todo_usecase(repo: ProjectRepository) -> FindTodoThroughProjectUseCase:
    """Factory function for creating FindTodoThroughProjectUseCase."""
    return FindTodoThroughProjectUseCaseImpl(repo)
