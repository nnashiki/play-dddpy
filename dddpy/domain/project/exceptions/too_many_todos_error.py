"""Exception for too many todos in a project."""


class TooManyTodosError(Exception):
    """Exception raised when trying to add more todos than the allowed limit."""

    def __init__(self, current_count: int, max_count: int) -> None:
        self.current_count = current_count
        self.max_count = max_count
        super().__init__(
            f'Cannot add more todos. Current: {current_count}, Max allowed: {max_count}'
        )
