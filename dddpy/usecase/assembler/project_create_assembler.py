"""ProjectCreateAssembler for converting ProjectCreateDto to Project entity."""

from dddpy.domain.project.factories.project_factory import ProjectFactory
from dddpy.domain.project.value_objects import (
    ProjectName,
    ProjectDescription,
)
from dddpy.dto.project import ProjectCreateDto
from dddpy.domain.project.entities import Project


class ProjectCreateAssembler:
    """ProjectCreateDto → VO → ProjectFactory呼び出しを担当するアセンブラ
    
    アプリケーション層でDTOをドメインVOに変換し、
    ドメインFactoryを呼び出してエンティティを生成する責務を持つ。
    """

    @staticmethod
    def to_entity(dto: ProjectCreateDto) -> Project:
        """ProjectCreateDtoからProjectエンティティを生成
        
        Args:
            dto: Project作成用DTO
            
        Returns:
            Project: 生成されたProjectエンティティ
            
        Raises:
            ValueError: DTOの値が不正な場合
        """
        # 1) DTO → VO にパース
        name_vo = ProjectName(dto.name)
        description_vo = ProjectDescription(dto.description) if dto.description else None

        # 2) Factory でドメインエンティティ生成
        return ProjectFactory.create(
            name=name_vo,
            description=description_vo,
        )
