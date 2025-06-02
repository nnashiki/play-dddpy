"""TodoCreateAssembler for converting Todo creation DTOs to Todo entity."""

from typing import Protocol
from uuid import UUID

from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.factories.todo_factory import TodoFactory
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
    TodoId,
)
from dddpy.domain.shared.events import DomainEventPublisher
from dddpy.dto.todo import TodoCreateDto
from dddpy.domain.todo.entities import Todo


class TodoCreationData(Protocol):
    """Protocol for Todo creation data - allows various DTO types."""

    title: str
    description: str | None
    dependencies: list[str] | None


class TodoCreateAssembler:
    """Todo作成用DTOからTodoエンティティへの変換を担当するアセンブラ

    アプリケーション層でDTOをドメインVOに変換し、
    ドメインFactoryを呼び出してエンティティを生成する責務を持つ。

    Protocol対応により、TodoCreateDtoとAddTodoToProjectDto等、
    同じ構造を持つDTOを統一的に処理可能。
    """

    @staticmethod
    def to_entity(
        dto: TodoCreationData,
        project_id_str: str,
        event_publisher: DomainEventPublisher | None = None,
    ) -> Todo:
        """Todo作成用DTOからTodoエンティティを生成

        Args:
            dto: Todo作成用DTO（TodoCreateDto, AddTodoToProjectDto等対応）
            project_id_str: プロジェクトIDの文字列表現
            event_publisher: イベント発行用パブリッシャー

        Returns:
            Todo: 生成されたTodoエンティティ

        Raises:
            ValueError: DTOの値が不正な場合
        """
        return TodoCreateAssembler._create_todo_entity(
            title=dto.title,
            description=dto.description,
            dependencies=dto.dependencies,
            project_id_str=project_id_str,
            event_publisher=event_publisher,
        )

    @staticmethod
    def _create_todo_entity(
        title: str,
        description: str | None,
        dependencies: list[str] | None,
        project_id_str: str,
        event_publisher: DomainEventPublisher | None = None,
    ) -> Todo:
        """共通のTodo作成ロジック

        Args:
            title: Todoタイトル
            description: Todo説明（任意）
            dependencies: 依存Todo ID文字列リスト（任意）
            project_id_str: プロジェクトIDの文字列表現
            event_publisher: イベント発行用パブリッシャー（任意）

        Returns:
            Todo: 生成されたTodoエンティティ
        """
        # 1) 文字列 → VO/ID にパース
        project_id = ProjectId(UUID(project_id_str))
        title_vo = TodoTitle(title)
        description_vo = TodoDescription(description) if description else None

        # dependencies はリスト of str → List[TodoId] → TodoDependencies
        dependencies_vo = None
        if dependencies:
            dep_vo_list = [TodoId(UUID(dep_str)) for dep_str in dependencies]
            dependencies_vo = TodoDependencies.from_list(dep_vo_list)

        # 2) Factory でドメインエンティティ生成
        return TodoFactory.create(
            title=title_vo,
            project_id=project_id,
            description=description_vo,
            dependencies=dependencies_vo,
            event_publisher=event_publisher,
        )
