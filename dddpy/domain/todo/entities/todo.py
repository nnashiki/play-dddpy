"""This module provides the Todo entity representing a task or item to be completed."""

from datetime import datetime
from typing import Optional

from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription,
    TodoId,
    TodoStatus,
    TodoTitle,
)
from dddpy.domain.todo.exceptions import (
    TodoCircularDependencyError,
    TodoAlreadyCompletedError,
    TodoNotFoundError,
)


class Todo:
    """Todo entity representing a task or item to be completed"""

    def __init__(
        self,
        id: TodoId,
        title: TodoTitle,
        description: Optional[TodoDescription] = None,
        status: TodoStatus = TodoStatus.NOT_STARTED,
        dependencies: Optional[TodoDependencies] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ):
        """
        Initialize a new Todo entity.
        """
        self._id = id
        self._title = title
        self._description = description
        self._status = status
        self._dependencies = dependencies or TodoDependencies.empty()
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()
        self._completed_at = completed_at

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, Todo):
            return self.id == obj.id

        return False

    @property
    def id(self) -> TodoId:
        """Get the Todo's unique identifier"""
        return self._id

    @property
    def title(self) -> TodoTitle:
        """Get the Todo's title"""
        return self._title

    @property
    def description(self) -> Optional[TodoDescription]:
        """Get the Todo's description"""
        return self._description

    @property
    def status(self) -> TodoStatus:
        """Get the Todo's current status"""
        return self._status

    @property
    def created_at(self) -> datetime:
        """Get the Todo's creation timestamp"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get the Todo's last update timestamp"""
        return self._updated_at

    @property
    def completed_at(self) -> Optional[datetime]:
        """Get the Todo's completion timestamp"""
        return self._completed_at

    @property
    def dependencies(self) -> TodoDependencies:
        """Get the Todo's dependencies"""
        return self._dependencies

    def update_title(self, new_title: TodoTitle) -> None:
        """Update the Todo's title"""
        self._title = new_title
        self._updated_at = datetime.now()

    def update_description(self, new_description: Optional[TodoDescription]) -> None:
        """Update the Todo's description"""
        self._description = new_description if new_description else None
        self._updated_at = datetime.now()

    def _check_circular_dependency(self, new_dep_id: TodoId, get_todo_by_id) -> bool:
        """Check if adding new_dep_id would create a circular dependency using DFS"""
        visited = set()

        def has_path_to_self(current_id: TodoId) -> bool:
            if current_id == self._id:
                return True
            if current_id in visited:
                return False

            visited.add(current_id)

            try:
                current_todo = get_todo_by_id(current_id)
                for dep_id in current_todo.dependencies.values:
                    if has_path_to_self(dep_id):
                        return True
            except Exception:
                # If dependency todo is not found, ignore it
                pass

            return False

        return has_path_to_self(new_dep_id)

    def add_dependency(self, dep_id: TodoId, get_todo_by_id=None) -> None:
        """Add a dependency to this Todo"""
        if dep_id == self._id:
            raise ValueError('Cannot add self as dependency')

        if self._dependencies.contains(dep_id):
            return  # Already exists, no need to add

        # Check for circular dependency if get_todo_by_id is provided
        if get_todo_by_id and self._check_circular_dependency(dep_id, get_todo_by_id):
            raise TodoCircularDependencyError(
                f'Adding dependency {dep_id.value} would create a circular dependency'
            )

        self._dependencies = self._dependencies.add(dep_id)
        self._updated_at = datetime.now()

    def remove_dependency(self, dep_id: TodoId) -> None:
        """Remove a dependency from this Todo"""
        self._dependencies = self._dependencies.remove(dep_id)
        self._updated_at = datetime.now()

    def set_dependencies(
        self, dependencies: TodoDependencies, get_todo_by_id=None
    ) -> None:
        """Set the Todo's dependencies"""
        # Self-dependency check is now handled in TodoDependencies.from_list()
        # But we still need to check here in case someone creates TodoDependencies directly
        if dependencies.contains(self._id):
            raise ValueError('Cannot add self as dependency')

        # Check for circular dependencies if get_todo_by_id is provided
        if get_todo_by_id:
            for dep_id in dependencies.values:
                if self._check_circular_dependency(dep_id, get_todo_by_id):
                    raise TodoCircularDependencyError(
                        f'Setting dependency {dep_id.value} would create a circular dependency'
                    )

        self._dependencies = dependencies
        self._updated_at = datetime.now()

    def can_start(self, get_todo_by_id) -> bool:
        """Check if this Todo can be started (all dependencies are completed)"""
        if self._dependencies.is_empty():
            return True

        # Check if all dependencies are completed
        for dep_id in self._dependencies.values:
            try:
                dep_todo = get_todo_by_id(dep_id)
                if dep_todo is None or not dep_todo.is_completed:
                    return False
            except TodoNotFoundError:
                # If dependency todo is not found, consider it as not completed
                return False
            except Exception:
                # For any other unexpected exceptions, re-raise them
                # Don't hide potential system errors
                raise

        return True

    def start(self) -> None:
        """Change the Todo's status to in progress"""
        self._status = TodoStatus.IN_PROGRESS
        self._updated_at = datetime.now()

    def complete(self) -> None:
        """Change the Todo's status to completed"""
        if self._status == TodoStatus.COMPLETED:
            raise TodoAlreadyCompletedError()

        self._status = TodoStatus.COMPLETED
        self._completed_at = datetime.now()
        self._updated_at = self._completed_at

    @property
    def is_completed(self) -> bool:
        """Check if the Todo is completed"""
        return self._status == TodoStatus.COMPLETED

    def is_overdue(
        self, deadline: datetime, current_time: Optional[datetime] = None
    ) -> bool:
        """
        Check if the Todo is overdue based on the given deadline.
        A Todo is considered overdue if:
        1. It is not completed and the current time is past the deadline
        Note: Completed todos are never considered overdue

        Args:
            deadline: The deadline to check against
            current_time: The current time to use for comparison (defaults to now)
        """
        if self.is_completed:
            return False
        return (current_time or datetime.now()) > deadline

    @staticmethod
    def create(
        title: TodoTitle,
        description: Optional[TodoDescription] = None,
        dependencies: Optional[TodoDependencies] = None,
    ) -> 'Todo':
        """Create a new Todo"""
        return Todo(TodoId.generate(), title, description, dependencies=dependencies)
