"""Exception for when a self-dependency is attempted."""


class SelfDependencyError(Exception):
    """Exception for when a todo tries to add itself as a dependency."""

    message = 'Cannot add self as dependency'

    def __str__(self):
        return SelfDependencyError.message
