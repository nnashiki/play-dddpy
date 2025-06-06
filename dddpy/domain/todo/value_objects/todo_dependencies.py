"""Value object for Todo dependencies."""

from dataclasses import dataclass

from ..exceptions import SelfDependencyError, TooManyDependenciesError
from .todo_id import TodoId


@dataclass(frozen=True)
class TodoDependencies:
    """Value object representing dependencies of a Todo"""

    values: set[TodoId]

    def __post_init__(self) -> None:
        """Validate the dependencies after initialization"""
        if len(self.values) > 100:  # Maximum 100 dependencies
            raise TooManyDependenciesError()

    @staticmethod
    def empty() -> 'TodoDependencies':
        """Create an empty dependencies value object"""
        return TodoDependencies(set())

    @staticmethod
    def from_list(
        todo_ids: list[TodoId], self_id: TodoId | None = None
    ) -> 'TodoDependencies':
        """Create dependencies from a list of TodoIds (duplicates will be removed)

        Args:
            todo_ids: List of TodoId objects to create dependencies from
            self_id: Optional TodoId to check for self-dependency

        Raises:
            ValueError: If self_id is included in the dependencies
        """
        todo_id_set = set(todo_ids)

        if self_id and self_id in todo_id_set:
            raise SelfDependencyError()

        return TodoDependencies(todo_id_set)

    def add(self, todo_id: TodoId) -> 'TodoDependencies':
        """Add a dependency and return new instance"""
        new_values = self.values.copy()
        new_values.add(todo_id)
        return TodoDependencies(new_values)

    def remove(self, todo_id: TodoId) -> 'TodoDependencies':
        """Remove a dependency and return new instance"""
        new_values = self.values.copy()
        new_values.discard(todo_id)
        return TodoDependencies(new_values)

    def contains(self, todo_id: TodoId) -> bool:
        """Check if dependencies contain the given TodoId"""
        return todo_id in self.values

    def to_list(self) -> list[TodoId]:
        """Convert to list for external usage"""
        return list(self.values)

    def is_empty(self) -> bool:
        """Check if dependencies are empty"""
        return len(self.values) == 0

    def size(self) -> int:
        """Get the number of dependencies"""
        return len(self.values)
