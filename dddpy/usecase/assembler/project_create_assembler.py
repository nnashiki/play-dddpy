"""ProjectCreateAssembler for converting ProjectCreateDto to Project entity."""

from dddpy.dto.project import ProjectCreateDto
from dddpy.domain.project.entities import Project
from dddpy.domain.shared.events import DomainEventPublisher


class ProjectCreateAssembler:
    """ProjectCreateDto → Project 作成を担当するアセンブラ
    
    アプリケーション層でDTOからエンティティを生成する責務を持つ。
    """

    @staticmethod
    def to_entity(dto: ProjectCreateDto, event_publisher: DomainEventPublisher | None = None) -> Project:
        """ProjectCreateDtoからProjectエンティティを生成（イベント発行付き）
        
        Args:
            dto: Project作成用DTO
            event_publisher: イベント発行用パブリッシャー
            
        Returns:
            Project: 生成されたProjectエンティティ
            
        Raises:
            ValueError: DTOの値が不正な場合
        """
        return Project.create(
            name=dto.name,
            description=dto.description,
            event_publisher=event_publisher,
        )
