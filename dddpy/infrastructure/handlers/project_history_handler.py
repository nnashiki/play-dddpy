"""Project history event handler for saving project creation events to database."""

from sqlalchemy.orm import Session
from dddpy.domain.project.events.project_created_event import ProjectCreatedEvent
from dddpy.infrastructure.sqlite.project.project_history_model import (
    ProjectHistoryModel,
)
from uuid import uuid4


def on_project_created(event: ProjectCreatedEvent, session: Session) -> None:
    """Handle ProjectCreated event by saving project history to database."""
    session.add(
        ProjectHistoryModel(
            id=uuid4(),
            project_id=event.project_id,
            name=event.name,
            description=event.description,
            event_type='CREATED',
            recorded_at=int(event.occurred_at.timestamp() * 1000),
        )
    )
    # commitはUseCaseで行う
