"""Todo history event handler for saving todo creation events to database."""

from sqlalchemy.orm import Session
from dddpy.domain.todo.events import TodoCreatedEvent
from dddpy.infrastructure.sqlite.todo.todo_history_model import TodoHistoryModel
from uuid import uuid4


def on_todo_created(event: TodoCreatedEvent, session: Session) -> None:
    """Handle TodoCreated event by saving todo history to database."""
    session.add(
        TodoHistoryModel(
            id=uuid4(),
            todo_id=event.todo_id,
            project_id=event.project_id,
            title=event.title,
            description=event.description,
            event_type='CREATED',
            recorded_at=int(event.occurred_at.timestamp() * 1000),
        )
    )
    # commitはUseCaseで行う
