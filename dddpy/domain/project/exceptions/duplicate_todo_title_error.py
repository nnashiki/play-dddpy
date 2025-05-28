"""Exception for duplicate todo title."""


class DuplicateTodoTitleError(Exception):
    """Exception raised when trying to add a todo with a duplicate title."""

    def __init__(self, title: str) -> None:
        self.title = title
        super().__init__(f"Todo with title '{title}' already exists in this project")
