"""Project domain events."""

from .project_created_event import ProjectCreatedEvent
from .project_deleted_event import ProjectDeletedEvent

__all__ = [
    'ProjectCreatedEvent',
    'ProjectDeletedEvent',
]
