"""Exception raised when a circular dependency is detected."""


class TodoCircularDependencyError(Exception):
    """Exception raised when a circular dependency is detected in todo dependencies."""

    def __init__(self, message: str = 'Circular dependency detected'):
        self.message = message
        super().__init__(self.message)
