"""Domain service for Todo entity business logic (circular dependency, can_start, etc)."""

from typing import TYPE_CHECKING, List
from dddpy.domain.todo.value_objects import TodoId, TodoDependencies
from dddpy.domain.todo.exceptions import (
    TodoCircularDependencyError,
    TodoDependencyNotFoundError,
)

if TYPE_CHECKING:
    from dddpy.domain.todo.repositories import TodoRepository
    from dddpy.domain.todo.entities import Todo

__all__ = ['TodoDomainService']


class TodoDomainService:
    @staticmethod
    def has_circular_dependency(
        todo: 'Todo', new_dep_id: TodoId, todo_repository: 'TodoRepository'
    ) -> bool:
        """Check if adding a dependency would create a circular dependency"""
        visited = set()

        def dfs(current_id: TodoId) -> bool:
            if current_id == todo.id:
                return True
            if current_id in visited:
                return False
            visited.add(current_id)
            current_todo = todo_repository.find_by_id(current_id)
            if not current_todo:
                return False
            for dep_id in current_todo.dependencies.values:
                if dfs(dep_id):
                    return True
            return False

        return dfs(new_dep_id)

    @staticmethod
    def can_start(todo: 'Todo', todo_repository: 'TodoRepository') -> bool:
        """Check if a todo can be started (all dependencies are completed)"""
        if todo.dependencies.is_empty():
            return True
        for dep_id in todo.dependencies.values:
            dep_todo = todo_repository.find_by_id(dep_id)
            if not dep_todo or not dep_todo.is_completed:
                return False
        return True

    @staticmethod
    def validate_dependencies_exist(
        dependency_ids: List[TodoId], todo_repository: 'TodoRepository'
    ) -> None:
        """Validate that all dependency todos exist."""
        for dep_id in dependency_ids:
            if not todo_repository.find_by_id(dep_id):
                raise TodoDependencyNotFoundError(str(dep_id.value))

    @staticmethod
    def validate_no_circular_dependency(
        todo: 'Todo', new_dependencies: List[TodoId], todo_repository: 'TodoRepository'
    ) -> None:
        """Validate that setting new dependencies would not create circular dependencies."""
        # Create a temporary todo with new dependencies to simulate the future state
        temp_dependencies = TodoDependencies.from_list(
            new_dependencies, self_id=todo.id
        )

        for dep_id in new_dependencies:
            if TodoDomainService._has_circular_dependency_with_new_deps(
                todo.id, dep_id, temp_dependencies, todo_repository
            ):
                raise TodoCircularDependencyError(
                    f'Setting dependency {dep_id.value} would create a circular dependency'
                )

    @staticmethod
    def _has_circular_dependency_with_new_deps(
        original_todo_id: TodoId,
        new_dep_id: TodoId,
        new_dependencies: 'TodoDependencies',
        todo_repository: 'TodoRepository',
    ) -> bool:
        """Check if adding a dependency would create a circular dependency using new dependencies."""
        visited = set()

        def dfs(current_id: TodoId) -> bool:
            if current_id == original_todo_id:
                return True
            if current_id in visited:
                return False
            visited.add(current_id)

            current_todo = todo_repository.find_by_id(current_id)
            if not current_todo:
                return False

            # Use new dependencies if checking the original todo, otherwise use existing dependencies
            deps_to_check = (
                new_dependencies.values
                if current_id == original_todo_id
                else current_todo.dependencies.values
            )

            for dep_id in deps_to_check:
                if dfs(dep_id):
                    return True
            return False

        return dfs(new_dep_id)
