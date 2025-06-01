"""ProjectNotFoundError exception"""


class ProjectNotFoundError(Exception):
    """ProjectNotFoundError is an error that occurs when a Project is not found."""

    message = 'The Project you specified does not exist.'

    def __str__(self):
        return ProjectNotFoundError.message
