"""Todo domain events."""

from datetime import datetime
from typing import Any, Union
from uuid import UUID

from dddpy.domain.shared.events import DomainEvent


class TodoCreatedEvent(DomainEvent):
    """Event fired when a new Todo is created."""

    def __init__(
        self,
        todo_id: UUID,
        project_id: UUID,
        title: str,
        description: Union[str, None] = None,
        occurred_at: Union[datetime, None] = None,
    ) -> None:
        super().__init__(todo_id, occurred_at)
        self.todo_id = todo_id
        self.project_id = project_id
        self.title = title
        self.description = description

    @property
    def event_type(self) -> str:
        return 'TodoCreated'

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update(
            {
                'todo_id': str(self.todo_id),
                'project_id': str(self.project_id),
                'title': self.title,
                'description': self.description,
            }
        )
        return base_dict


class TodoStartedEvent(DomainEvent):
    """Event fired when a Todo is started."""

    def __init__(
        self,
        todo_id: UUID,
        project_id: UUID,
        title: str,
        occurred_at: Union[datetime, None] = None,
    ) -> None:
        super().__init__(todo_id, occurred_at)
        self.todo_id = todo_id
        self.project_id = project_id
        self.title = title

    @property
    def event_type(self) -> str:
        return 'TodoStarted'

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update(
            {
                'todo_id': str(self.todo_id),
                'project_id': str(self.project_id),
                'title': self.title,
            }
        )
        return base_dict


class TodoUpdatedEvent(DomainEvent):
    """Event fired when a Todo is updated."""

    def __init__(
        self,
        todo_id: UUID,
        project_id: UUID,
        title: str,
        description: Union[str, None] = None,
        dependencies: Union[list[str], None] = None,
        occurred_at: Union[datetime, None] = None,
    ) -> None:
        super().__init__(todo_id, occurred_at)
        self.todo_id = todo_id
        self.project_id = project_id
        self.title = title
        self.description = description
        self.dependencies = dependencies or []

    @property
    def event_type(self) -> str:
        return 'TodoUpdated'

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update(
            {
                'todo_id': str(self.todo_id),
                'project_id': str(self.project_id),
                'title': self.title,
                'description': self.description,
                'dependencies': self.dependencies,
            }
        )
        return base_dict


class TodoCompletedEvent(DomainEvent):
    """Event fired when a Todo is completed."""

    def __init__(
        self,
        todo_id: UUID,
        project_id: UUID,
        title: str,
        occurred_at: Union[datetime, None] = None,
    ) -> None:
        super().__init__(todo_id, occurred_at)
        self.todo_id = todo_id
        self.project_id = project_id
        self.title = title

    @property
    def event_type(self) -> str:
        return 'TodoCompleted'

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update(
            {
                'todo_id': str(self.todo_id),
                'project_id': str(self.project_id),
                'title': self.title,
            }
        )
        return base_dict


class TodoAddedToProjectEvent(DomainEvent):
    """Event fired when a Todo is added to a Project."""

    def __init__(
        self,
        project_id: UUID,
        todo_id: UUID,
        todo_title: str,
        occurred_at: Union[datetime, None] = None,
    ) -> None:
        super().__init__(project_id, occurred_at)
        self.project_id = project_id
        self.todo_id = todo_id
        self.todo_title = todo_title

    @property
    def event_type(self) -> str:
        return 'TodoAddedToProject'

    def to_dict(self) -> dict[str, Any]:
        base_dict = super().to_dict()
        base_dict.update(
            {
                'project_id': str(self.project_id),
                'todo_id': str(self.todo_id),
                'todo_title': self.todo_title,
            }
        )
        return base_dict
