"""Enhanced TodoCreateAssembler with event publishing support."""

from uuid import UUID

from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.factories.event_aware_todo_factory import EventAwareTodoFactory
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
    TodoId,
)
from dddpy.usecase.assembler.todo_create_assembler import TodoCreationData
from dddpy.domain.todo.entities import Todo


class EventAwareTodoCreateAssembler:
    """EventAware版TodoCreateAssembler - ドメインイベント発行付き
    
    このAssemblerはEventAwareTodoFactoryを使用して、
    Todo作成時にドメインイベントを自動発行します。
    
    Protocol対応により、TodoCreateDtoとAddTodoToProjectDto等、
    同じ構造を持つDTOを統一的に処理可能。
    """

    @staticmethod
    def to_entity(dto: TodoCreationData, project_id_str: str) -> Todo:
        """Todo作成用DTOからTodoエンティティを生成（イベント発行付き）
        
        Args:
            dto: Todo作成用DTO（TodoCreateDto, AddTodoToProjectDto等対応）
            project_id_str: プロジェクトIDの文字列表現
            
        Returns:
            Todo: 生成されたTodoエンティティ（イベント発行済み）
            
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

        # 2) EventAwareFactory でドメインエンティティ生成（イベント自動発行）
        return EventAwareTodoFactory.create(
            title=title_vo,
            project_id=project_id,
            description=description_vo,
            dependencies=dependencies_vo,
        )
