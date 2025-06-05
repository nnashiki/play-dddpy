"""Use case for finding a todo through project."""

from abc import ABC, abstractmethod
from uuid import UUID

from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.todo.value_objects import TodoId
from dddpy.dto.todo import TodoOutputDto
from dddpy.infrastructure.sqlite.project.project_repository import new_project_repository
from dddpy.infrastructure.sqlite.uow import SqlAlchemyUnitOfWork
from dddpy.usecase.converter.todo_converter import TodoConverter


class FindTodoThroughProjectUseCase(ABC):
    """Abstract base class for find todo through project use case."""

    @abstractmethod
    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """Execute the find todo through project use case."""
        ...


class FindTodoThroughProjectUseCaseImpl(FindTodoThroughProjectUseCase):
    """UoW-based implementation of find todo through project use case."""

    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(self, project_id: str, todo_id: str) -> TodoOutputDto:
        """Execute the find todo through project use case."""
        from dddpy.domain.project.value_objects import ProjectId

        result: TodoOutputDto
        with self.uow as uow:
            if uow.session is None:
                raise RuntimeError('UoW was not properly initialized')
            
            _project_id = ProjectId(UUID(project_id))
            _todo_id = TodoId(UUID(todo_id))

            project_repository = new_project_repository(uow.session)
            project = project_repository.find_by_id(_project_id)
            if project is None:
                from dddpy.domain.project.exceptions import ProjectNotFoundError
                raise ProjectNotFoundError()

            todo = project.get_todo(_todo_id)
            result = TodoConverter.to_output_dto(todo)
        return result



def new_find_todo_usecase(uow: SqlAlchemyUnitOfWork) -> FindTodoThroughProjectUseCase:
    """Factory function for creating FindTodoThroughProjectUseCase with UoW."""
    return FindTodoThroughProjectUseCaseImpl(uow)
