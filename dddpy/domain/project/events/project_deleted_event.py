"""Project deletion event."""

from datetime import datetime
from typing import Any, Union
from uuid import UUID

from dddpy.domain.shared.events import DomainEvent


class ProjectDeletedEvent(DomainEvent):
    """Event fired when a Project is deleted."""

    def __init__(
        self,
        project_id: UUID,
        name: str,
        description: Union[str, None] = None,
        occurred_at: Union[datetime, None] = None,
    ) -> None:
        super().__init__(project_id, occurred_at)
        self.project_id = project_id
        self.name = name
        self.description = description

    @property
    def event_type(self) -> str:
        return 'ProjectDeleted'

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update(
            {
                'project_id': str(self.project_id),
                'name': self.name,
                'description': self.description,
            }
        )
        return base_dict
