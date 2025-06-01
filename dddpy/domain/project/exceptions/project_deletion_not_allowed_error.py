"""Exception for when a project cannot be deleted due to dependencies."""


class ProjectDeletionNotAllowedError(Exception):
    """Exception for when a project cannot be deleted due to dependencies."""

    def __init__(self, reason: str = 'Project cannot be deleted'):
        self.message = reason
        super().__init__(self.message)

    def __str__(self):
        return self.message
