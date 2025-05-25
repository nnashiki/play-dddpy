"""Exception raised when dependencies are not satisfied."""


class TodoDependencyNotCompletedError(Exception):
    """Exception raised when trying to start a todo with incomplete dependencies."""

    def __init__(self, message: str = 'Dependencies are not completed'):
        self.message = message
        super().__init__(self.message)
