"""This module provides use case for completing a Todo entity."""

from abc import ABC, abstractmethod

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import (
    TodoNotFoundError,
)
from dddpy.domain.todo.repositories import TodoRepository
from dddpy.domain.todo.value_objects import TodoId


class CompleteTodoUseCase(ABC):
    """CompleteTodoUseCase defines an interface for completing a Todo."""

    @abstractmethod
    def execute(self, todo_id: TodoId) -> Todo:
        """execute completes a Todo."""


class CompleteTodoUseCaseImpl(CompleteTodoUseCase):
    """CompleteTodoUseCaseImpl implements the use case for completing a Todo."""

    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    def execute(self, todo_id: TodoId) -> Todo:
        """execute completes a Todo."""
        todo = self.todo_repository.find_by_id(todo_id)

        if todo is None:
            raise TodoNotFoundError

        # Entity will enforce state transition rules
        todo.complete()
        self.todo_repository.save(todo)
        return todo


def new_complete_todo_usecase(todo_repository: TodoRepository) -> CompleteTodoUseCase:
    """Create a new instance of CompleteTodoUseCase."""
    return CompleteTodoUseCaseImpl(todo_repository)
