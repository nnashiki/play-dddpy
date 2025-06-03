"""ProjectFactory for creating Project entities with domain value objects."""

from typing import TYPE_CHECKING, Union

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import (
    ProjectName,
    ProjectDescription,
)
from dddpy.domain.shared.clock import Clock, SystemClock

if TYPE_CHECKING:
    from dddpy.domain.shared.events import DomainEventPublisher


class ProjectFactory:
    """ドメイン層のProjectFactory: ドメインVOのみを受け取りProjectエンティティを生成"""

    @staticmethod
    def create(
        name: ProjectName,
        description: ProjectDescription | None = None,
        clock: Clock | None = None,
        event_publisher: Union['DomainEventPublisher', None] = None,
    ) -> Project:
        """ドメインVOからProjectエンティティを生成

        Args:
            name: プロジェクトの名前
            description: プロジェクトの説明（任意）
            clock: 時刻取得用クロック（任意、デフォルトはSystemClock）
            event_publisher: イベント発行用パブリッシャー（任意）

        Returns:
            Project: 生成されたProjectエンティティ
        """
        return Project.create(
            name=name.value,
            description=description.value if description else None,
            event_publisher=event_publisher,
        )
