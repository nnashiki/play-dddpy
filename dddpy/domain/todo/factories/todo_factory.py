"""TodoFactory for creating Todo entities with domain value objects."""

from typing import TYPE_CHECKING

from dddpy.domain.shared.clock import Clock, SystemClock
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
)

if TYPE_CHECKING:
    from dddpy.domain.project.value_objects import ProjectId


class TodoFactory:
    """ドメイン層のTodoFactory: ドメインVOのみを受け取りTodoエンティティを生成"""

    @staticmethod
    def create(
        title: TodoTitle,
        project_id: 'ProjectId',
        description: TodoDescription | None = None,
        dependencies: TodoDependencies | None = None,
        clock: Clock | None = None,
    ) -> Todo:
        """ドメインVOからTodoエンティティを生成
        
        Args:
            title: Todoのタイトル
            project_id: 所属するプロジェクトのID
            description: Todoの説明（任意）
            dependencies: Todoの依存関係（任意）
            clock: 時刻取得用クロック（任意、デフォルトはSystemClock）
            
        Returns:
            Todo: 生成されたTodoエンティティ
        """
        return Todo.create(
            title=title,
            project_id=project_id,
            description=description,
            dependencies=dependencies,
            clock=clock or SystemClock(),
        )
