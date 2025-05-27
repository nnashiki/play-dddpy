"""Exception for when too many dependencies are specified."""


class TooManyDependenciesError(Exception):
    """Exception for when too many dependencies are specified for a Todo."""

    message = 'Too many dependencies. Maximum 100 dependencies allowed.'

    def __str__(self):
        return TooManyDependenciesError.message
