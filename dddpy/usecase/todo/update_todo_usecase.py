"""This module provides use case for updating a Todo entity."""

from abc import ABC, abstractmethod
from typing import Optional, List

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import TodoNotFoundError
from dddpy.domain.todo.repositories import TodoRepository
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription,
    TodoId,
    TodoTitle,
)


class UpdateTodoUseCase(ABC):
    """UpdateTodoUseCase defines an interface for updating a Todo."""

    @abstractmethod
    def execute(
        self,
        todo_id: TodoId,
        title: Optional[TodoTitle] = None,
        description: Optional[TodoDescription] = None,
        dependencies: Optional[List[TodoId]] = None,
    ) -> Todo:
        """execute updates a Todo."""


class UpdateTodoUseCaseImpl(UpdateTodoUseCase):
    """UpdateTodoUseCaseImpl implements the use case for updating a Todo."""

    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    def execute(
        self,
        todo_id: TodoId,
        title: Optional[TodoTitle] = None,
        description: Optional[TodoDescription] = None,
        dependencies: Optional[List[TodoId]] = None,
    ) -> Todo:
        """execute updates a Todo."""
        todo = self.todo_repository.find_by_id(todo_id)

        if todo is None:
            raise TodoNotFoundError

        if title is not None:
            todo.update_title(title)
        if description is not None:
            todo.update_description(description)
        if dependencies is not None:
            todo_dependencies = TodoDependencies.from_list(
                dependencies, self_id=todo_id
            )
            # Note: We could add circular dependency checking here by passing a get_todo_by_id function
            todo.set_dependencies(todo_dependencies)

        self.todo_repository.save(todo)
        return todo


def new_update_todo_usecase(todo_repository: TodoRepository) -> UpdateTodoUseCase:
    """Create a new instance of UpdateTodoUseCase."""
    return UpdateTodoUseCaseImpl(todo_repository)
