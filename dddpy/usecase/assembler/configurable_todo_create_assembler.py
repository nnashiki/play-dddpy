"""Configurable TodoCreateAssembler with strategy selection."""

from uuid import UUID

from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.factories import TodoFactorySelector, TodoCreationStrategy
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
    TodoId,
)
from dddpy.usecase.assembler.todo_create_assembler import TodoCreationData
from dddpy.domain.todo.entities import Todo


class ConfigurableTodoCreateAssembler:
    """設定可能なTodoCreateAssembler - 作成戦略を選択可能

    このAssemblerは作成コンテキストに応じて適切なFactory戦略を選択し、
    Todoエンティティを生成します。

    Protocol対応により、TodoCreateDtoとAddTodoToProjectDto等、
    同じ構造を持つDTOを統一的に処理可能。
    """

    @staticmethod
    def to_entity(
        dto: TodoCreationData,
        project_id_str: str,
        strategy: TodoCreationStrategy | None = None,
        auto_select_strategy: bool = True,
    ) -> Todo:
        """Todo作成用DTOからTodoエンティティを生成（戦略選択可能）

        Args:
            dto: Todo作成用DTO（TodoCreateDto, AddTodoToProjectDto等対応）
            project_id_str: プロジェクトIDの文字列表現
            strategy: 使用する作成戦略（Noneの場合は自動選択）
            auto_select_strategy: 自動戦略選択を有効にするか

        Returns:
            Todo: 生成されたTodoエンティティ

        Raises:
            ValueError: DTOの値が不正な場合
        """
        # 1) DTO → VO/ID にパース
        project_id = ProjectId(UUID(project_id_str))
        title_vo = TodoTitle(dto.title)
        description_vo = TodoDescription(dto.description) if dto.description else None

        # dependencies はリスト of str → List[TodoId] → TodoDependencies
        dependencies_vo = None
        if dto.dependencies:
            dep_vo_list = [TodoId(UUID(dep_str)) for dep_str in dto.dependencies]
            dependencies_vo = TodoDependencies.from_list(dep_vo_list)

        # 2) 戦略決定
        if strategy is None and auto_select_strategy:
            strategy = TodoFactorySelector.get_recommended_strategy(
                has_dependencies=bool(dto.dependencies),
                is_high_priority=ConfigurableTodoCreateAssembler._is_high_priority(dto),
                needs_events=True,  # デフォルトでイベント発行を有効
            )
        elif strategy is None:
            strategy = TodoCreationStrategy.STANDARD

        # 3) 選択された戦略でTodo生成
        return TodoFactorySelector.create_todo(
            strategy=strategy,
            title=title_vo,
            project_id=project_id,
            description=description_vo,
            dependencies=dependencies_vo,
        )

    @staticmethod
    def _is_high_priority(dto: TodoCreationData) -> bool:
        """DTOから高優先度タスクかどうかを判定

        Args:
            dto: Todo作成用DTO

        Returns:
            bool: 高優先度タスクかどうか
        """
        # 簡単な判定ロジック（実際の実装では、より複雑な判定が可能）
        if not dto.title:
            return False

        high_priority_keywords = ['urgent', '緊急', 'critical', '重要', 'asap', '至急']
        title_lower = dto.title.lower()

        return any(keyword in title_lower for keyword in high_priority_keywords)

    @staticmethod
    def to_entity_with_explicit_strategy(
        dto: TodoCreationData,
        project_id_str: str,
        strategy: TodoCreationStrategy,
    ) -> Todo:
        """明示的な戦略指定でTodoエンティティを生成

        Args:
            dto: Todo作成用DTO（TodoCreateDto, AddTodoToProjectDto等対応）
            project_id_str: プロジェクトIDの文字列表現
            strategy: 使用する作成戦略

        Returns:
            Todo: 生成されたTodoエンティティ
        """
        return ConfigurableTodoCreateAssembler.to_entity(
            dto=dto,
            project_id_str=project_id_str,
            strategy=strategy,
            auto_select_strategy=False,
        )
