"""Event handler setup for registering domain event handlers with the dispatcher."""

from dddpy.domain.shared.events import get_event_dispatcher
from dddpy.domain.project.events.project_created_event import ProjectCreatedEvent
from dddpy.domain.todo.events import TodoCreatedEvent
from dddpy.infrastructure.handlers.project_history_handler import on_project_created
from dddpy.infrastructure.handlers.todo_history_handler import on_todo_created


def setup_event_handlers() -> None:
    """Register all event handlers with the global event dispatcher."""
    dispatcher = get_event_dispatcher()

    # Register project event handlers
    dispatcher.register(ProjectCreatedEvent, on_project_created)

    # Register todo event handlers
    dispatcher.register(TodoCreatedEvent, on_todo_created)

    print('Event handlers registered successfully')


def initialize_event_system() -> None:
    """Initialize the complete event system.

    This function should be called at application startup to ensure
    all event handlers are properly registered with the dispatcher.
    """
    setup_event_handlers()
