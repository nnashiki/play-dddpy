"""Raised when a dependency Todo does not exist."""


class TodoDependencyNotFoundError(Exception):
    """Raised when a dependency Todo does not exist."""

    def __init__(self, dep_id: str):
        """Initialize with the dependency id that was not found."""
        super().__init__(f'Dependency todo with id {dep_id} not found')
        self.message = f'Dependency todo with id {dep_id} not found'
