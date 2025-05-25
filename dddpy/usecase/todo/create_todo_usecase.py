"""This module provides use case for creating a new Todo entity."""

from abc import abstractmethod
from typing import Optional, List

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import TodoCircularDependencyError
from dddpy.domain.todo.repositories import TodoRepository
from dddpy.domain.todo.services.todo_domain_service import TodoDomainService
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription,
    TodoId,
    TodoTitle,
)


class CreateTodoUseCase:
    """CreateTodoUseCase defines a use case interface for creating a new Todo."""

    @abstractmethod
    def execute(
        self,
        title: TodoTitle,
        description: Optional[TodoDescription] = None,
        dependencies: Optional[List[TodoId]] = None,
    ) -> Todo:
        """execute creates a new Todo."""


class CreateTodoUseCaseImpl(CreateTodoUseCase):
    """CreateTodoUseCaseImpl implements the use case for creating a new Todo."""

    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    def execute(
        self,
        title: TodoTitle,
        description: Optional[TodoDescription] = None,
        dependencies: Optional[List[TodoId]] = None,
    ) -> Todo:
        """execute creates a new Todo."""
        # Convert dependencies list to TodoDependencies value object
        todo_dependencies = None
        if dependencies:
            # Check that all dependencies exist before creating
            TodoDomainService.validate_dependencies_exist(
                dependencies, self.todo_repository
            )
            todo_dependencies = TodoDependencies.from_list(dependencies)

        # Note: Todo.create() already sets the dependencies, so no need to add them again
        # This avoids double updating the updated_at timestamp
        todo = Todo.create(
            title=title, description=description, dependencies=todo_dependencies
        )

        # Check for circular dependencies after creating the todo object
        if dependencies:
            TodoDomainService.validate_no_circular_dependency(
                todo, dependencies, self.todo_repository
            )

        self.todo_repository.save(todo)
        return todo


def new_create_todo_usecase(todo_repository: TodoRepository) -> CreateTodoUseCase:
    """Create a new instance of CreateTodoUseCase."""
    return CreateTodoUseCaseImpl(todo_repository)
