"""Project creation event."""

from datetime import datetime
from typing import Any
from uuid import UUID

from dddpy.domain.shared.events import DomainEvent


class ProjectCreatedEvent(DomainEvent):
    """Event fired when a new Project is created."""
    
    def __init__(
        self,
        project_id: UUID,
        name: str,
        description: str | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        super().__init__(project_id, occurred_at)
        self.project_id = project_id
        self.name = name
        self.description = description
    
    @property
    def event_type(self) -> str:
        return "ProjectCreated"
    
    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update({
            'project_id': str(self.project_id),
            'name': self.name,
            'description': self.description,
        })
        return base_dict
