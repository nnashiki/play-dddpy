"""ProjectFactory for creating Project entities with domain value objects."""

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import (
    ProjectName,
    ProjectDescription,
)
from dddpy.domain.shared.clock import Clock, SystemClock


class ProjectFactory:
    """ドメイン層のProjectFactory: ドメインVOのみを受け取りProjectエンティティを生成"""

    @staticmethod
    def create(
        name: ProjectName,
        description: ProjectDescription | None = None,
        clock: Clock | None = None,
    ) -> Project:
        """ドメインVOからProjectエンティティを生成
        
        Args:
            name: プロジェクトの名前
            description: プロジェクトの説明（任意）
            clock: 時刻取得用クロック（任意、デフォルトはSystemClock）
            
        Returns:
            Project: 生成されたProjectエンティティ
        """
        return Project.create(
            name=name.value,
            description=description.value if description else None,
        )
