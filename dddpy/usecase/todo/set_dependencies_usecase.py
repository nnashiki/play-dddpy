"""This module provides use case for setting dependencies of a Todo entity."""

from abc import ABC, abstractmethod
from typing import List

from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import TodoNotFoundError, TodoCircularDependencyError
from dddpy.domain.todo.repositories import TodoRepository
from dddpy.domain.todo.services.todo_domain_service import TodoDomainService
from dddpy.domain.todo.value_objects import TodoDependencies, TodoId


class SetDependenciesUseCase(ABC):
    """SetDependenciesUseCase defines an interface for setting Todo dependencies."""

    @abstractmethod
    def execute(self, todo_id: TodoId, dependencies: List[TodoId]) -> Todo:
        """execute sets dependencies for a Todo."""


class SetDependenciesUseCaseImpl(SetDependenciesUseCase):
    """SetDependenciesUseCaseImpl implements the use case for setting Todo dependencies."""

    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    def execute(self, todo_id: TodoId, dependencies: List[TodoId]) -> Todo:
        """execute sets dependencies for a Todo."""
        todo = self.todo_repository.find_by_id(todo_id)

        if todo is None:
            raise TodoNotFoundError

        # Check that all dependencies exist
        TodoDomainService.validate_dependencies_exist(
            dependencies, self.todo_repository
        )

        # Convert list to TodoDependencies value object
        todo_dependencies = TodoDependencies.from_list(dependencies, self_id=todo_id)

        # Check for circular dependencies before setting
        TodoDomainService.validate_no_circular_dependency(
            todo, dependencies, self.todo_repository
        )

        # Set dependencies (this will validate for self-dependency)
        todo.set_dependencies(todo_dependencies)

        self.todo_repository.save(todo)
        return todo


def new_set_dependencies_usecase(
    todo_repository: TodoRepository,
) -> SetDependenciesUseCase:
    """Create a new instance of SetDependenciesUseCase."""
    return SetDependenciesUseCaseImpl(todo_repository)
