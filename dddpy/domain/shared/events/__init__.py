"""Domain events infrastructure."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Type, TYPE_CHECKING
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


class DomainEvent(ABC):
    """Base class for all domain events."""
    
    def __init__(self, aggregate_id: UUID, occurred_at: datetime | None = None) -> None:
        self.event_id = uuid4()
        self.aggregate_id = aggregate_id
        self.occurred_at = occurred_at or datetime.now()
    
    @property
    @abstractmethod
    def event_type(self) -> str:
        """Get the event type identifier."""
    
    def to_dict(self) -> dict[str, Any]:
        """Convert event to dictionary representation."""
        return {
            'event_id': str(self.event_id),
            'event_type': self.event_type,
            'aggregate_id': str(self.aggregate_id),
            'occurred_at': self.occurred_at.isoformat(),
        }


class EventDispatcher:
    """Event dispatcher for registering and dispatching domain events."""
    
    def __init__(self) -> None:
        self._handlers: dict[Type[DomainEvent], list[Callable[[DomainEvent], None]]] = {}
    
    def register(self, event_type: Type[DomainEvent], handler: Callable[[DomainEvent], None]) -> None:
        """Register an event handler for a specific event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def dispatch(self, event: DomainEvent, session: 'Session | None' = None) -> None:
        """Dispatch an event to all registered handlers."""
        event_type = type(event)
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                try:
                    # Try to call handler with session if it accepts it
                    import inspect
                    sig = inspect.signature(handler)
                    if len(sig.parameters) == 2 and session is not None:
                        handler(event, session)
                    else:
                        handler(event)
                except Exception as e:
                    # Log error but don't fail the main operation
                    print(f"Error handling event {event_type.__name__}: {e}")


class DomainEventPublisher:
    """Simple domain event publisher for collecting and publishing events."""
    
    def __init__(self) -> None:
        self._events: list[DomainEvent] = []
        self._dispatcher: EventDispatcher | None = None
    
    def set_dispatcher(self, dispatcher: EventDispatcher) -> None:
        """Set the event dispatcher for immediate event handling."""
        self._dispatcher = dispatcher
    
    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event (collect for later processing and dispatch immediately if dispatcher is set)."""
        self._events.append(event)
        if self._dispatcher:
            self._dispatcher.dispatch(event)
    
    def get_events(self) -> list[DomainEvent]:
        """Get all published events."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all published events."""
        self._events.clear()


# Global instances
_event_dispatcher: EventDispatcher = EventDispatcher()
_event_publisher: DomainEventPublisher = DomainEventPublisher()

# Connect publisher and dispatcher
_event_publisher.set_dispatcher(_event_dispatcher)


def get_event_publisher() -> DomainEventPublisher:
    """Get the global event publisher instance."""
    return _event_publisher


def get_event_dispatcher() -> EventDispatcher:
    """Get the global event dispatcher instance."""
    return _event_dispatcher
