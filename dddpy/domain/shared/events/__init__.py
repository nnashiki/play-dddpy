"""Domain events infrastructure."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4


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


class DomainEventPublisher:
    """Simple domain event publisher for collecting and publishing events."""
    
    def __init__(self) -> None:
        self._events: list[DomainEvent] = []
    
    def publish(self, event: DomainEvent) -> None:
        """Publish a domain event (collect for later processing)."""
        self._events.append(event)
    
    def get_events(self) -> list[DomainEvent]:
        """Get all published events."""
        return self._events.copy()
    
    def clear_events(self) -> None:
        """Clear all published events."""
        self._events.clear()


# Global event publisher instance
_event_publisher: DomainEventPublisher = DomainEventPublisher()


def get_event_publisher() -> DomainEventPublisher:
    """Get the global event publisher instance."""
    return _event_publisher
