"""Event-aware Todo Factory for creating Todos with domain event publishing."""

from typing import TYPE_CHECKING

from dddpy.domain.shared.clock import Clock, SystemClock
from dddpy.domain.shared.events import get_event_publisher
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.events import TodoCreatedEvent
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
)

if TYPE_CHECKING:
    from dddpy.domain.project.value_objects import ProjectId


class EventAwareTodoFactory:
    """Event-aware TodoFactory that publishes domain events when creating Todos."""

    @staticmethod
    def create(
        title: TodoTitle,
        project_id: 'ProjectId',
        description: TodoDescription | None = None,
        dependencies: TodoDependencies | None = None,
        clock: Clock | None = None,
    ) -> Todo:
        """Create a Todo entity and publish TodoCreatedEvent.
        
        Args:
            title: Todoのタイトル
            project_id: 所属するプロジェクトのID
            description: Todoの説明（任意）
            dependencies: Todoの依存関係（任意）
            clock: 時刻取得用クロック（任意、デフォルトはSystemClock）
            
        Returns:
            Todo: 生成されたTodoエンティティ
        """
        # Create todo using standard creation logic
        todo = Todo.create(
            title=title,
            project_id=project_id,
            description=description,
            dependencies=dependencies,
            clock=clock or SystemClock(),
        )
        
        # Publish domain event
        event_publisher = get_event_publisher()
        event = TodoCreatedEvent(
            todo_id=todo.id.value,
            project_id=project_id.value,
            title=title.value,
            description=description.value if description else None,
            occurred_at=todo.created_at,
        )
        event_publisher.publish(event)
        
        return todo
