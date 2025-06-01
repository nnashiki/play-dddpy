"""Exception for when a todo cannot be removed due to dependencies."""


class TodoRemovalNotAllowedError(Exception):
    """Exception for when a todo cannot be removed because other todos depend on it."""

    def __init__(self, todo_id: str, dependent_todos: list[str]):
        self.todo_id = todo_id
        self.dependent_todos = dependent_todos
        self.message = f'Cannot remove todo {todo_id} because it is a dependency of: {", ".join(dependent_todos)}'
        super().__init__(self.message)

    def __str__(self):
        return self.message
