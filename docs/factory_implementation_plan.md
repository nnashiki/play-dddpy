# Factory実装方針

## 1. Factory配置の基本方針

DDDの原則に従い、以下の構造でFactoryを実装します：

- **ドメイン層のFactory**: ドメインVOのみを受け取り、エンティティを生成
- **アプリケーション層のAssembler**: DTOをVOに変換し、ドメインFactoryを呼び出し

## 2. ドメイン層Factory実装

### 2.1 TodoFactory
```
dddpy/domain/todo/factories/
└── todo_factory.py
```

- **責務**: ドメインVO（TodoTitle、TodoDescription等）からTodoエンティティを生成
- **原則**: DTOに一切依存せず、ドメインプリミティブのみを扱う
- **既存コード**: Todo.create()メソッドは残し、Factoryと並行運用

### 2.2 ProjectFactory
```
dddpy/domain/project/factories/
└── project_factory.py
```

- **責務**: ドメインVO（ProjectName、ProjectDescription等）からProjectエンティティを生成
- **既存コード**: Project.create()メソッドは残し、Factoryと並行運用

## 3. アプリケーション層Assembler実装

### 3.1 Entity作成用Assembler
```
dddpy/usecase/assembler/
├── todo_create_assembler.py      # TodoCreateDto → VO → TodoFactory
└── project_create_assembler.py   # ProjectCreateDto → VO → ProjectFactory
```

- **責務**: DTO → VO変換 → ドメインFactory呼び出し
- **命名**: 既存のpresentation層のAssemblerと区別するため「CreateAssembler」の命名

### 3.2 既存Converter/Assemblerとの共存
- **既存Converter**: Entity ↔ OutputDTO変換に継続使用
- **既存presentation/assembler**: OutputDTO → Schema変換に継続使用
- **新規Assembler**: InputDTO → Entity生成に特化

## 4. 段階的移行戦略

### 4.1 第1段階：Factory/Assembler追加
- ドメイン層にFactory追加
- アプリケーション層にCreateAssembler追加
- 既存コードの動作を保証

### 4.2 第2段階：UseCase修正
- 新しいAssemblerを使用するように段階的に移行
- 既存のTodo.create()、Project.create()は保持

### 4.3 第3段階：最適化
- 必要に応じて既存create()メソッドのFactory移行を検討

## 5. ディレクトリ構造

```
dddpy/
├── domain/
│   ├── todo/
│   │   ├── factories/           # 新規追加
│   │   │   └── todo_factory.py
│   │   └── entities/
│   └── project/
│       ├── factories/           # 新規追加
│       │   └── project_factory.py
│       └── entities/
├── usecase/
│   ├── assembler/               # 新規追加
│   │   ├── todo_create_assembler.py
│   │   └── project_create_assembler.py
│   └── converter/               # 既存継続
│       └── todo_converter.py
└── presentation/
    └── assembler/               # 既存継続
        └── project_assembler.py
```

## 6. 実装の利点

1. **ドメイン純粋性**: Factory層がDTOに依存しない
2. **テスト容易性**: ドメイン層のみの単体テストが可能
3. **責務分離**: DTO処理とドメイン生成の明確な分離
4. **段階的移行**: 既存コードを壊さずに新構造導入

この方針により、DDDの原則に従いつつ、既存システムとの互換性を保った実装が可能になります。

## 7. 実装例

### 7.1 TodoFactory (ドメイン層)

```python
# dddpy/domain/todo/factories/todo_factory.py

from dddpy.domain.shared.clock import Clock, SystemClock
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
)
from dddpy.domain.project.value_objects import ProjectId


class TodoFactory:
    """ドメイン層のTodoFactory: ドメインVOのみを受け取りTodoエンティティを生成"""

    @staticmethod
    def create(
        title: TodoTitle,
        project_id: ProjectId,
        description: TodoDescription | None = None,
        dependencies: TodoDependencies | None = None,
        clock: Clock | None = None,
    ) -> Todo:
        """ドメインVOからTodoエンティティを生成"""
        return Todo.create(
            title=title,
            project_id=project_id,
            description=description,
            dependencies=dependencies,
            clock=clock or SystemClock(),
        )
```

### 7.2 TodoCreateAssembler (アプリケーション層)

```python
# dddpy/usecase/assembler/todo_create_assembler.py

from uuid import UUID
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.factories.todo_factory import TodoFactory
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
    TodoId,
)
from dddpy.dto.todo import TodoCreateDto
from dddpy.domain.todo.entities import Todo


class TodoCreateAssembler:
    """TodoCreateDto → VO → TodoFactory呼び出しを担当"""

    @staticmethod
    def to_entity(dto: TodoCreateDto, project_id_str: str) -> Todo:
        """TodoCreateDtoからTodoエンティティを生成"""
        # 1) DTO → VO/ID にパース
        project_id = ProjectId(UUID(project_id_str))
        title_vo = TodoTitle(dto.title)
        description_vo = TodoDescription(dto.description) if dto.description else None

        # dependencies はリスト of str → List[TodoId] → TodoDependencies
        dependencies_vo = None
        if dto.dependencies:
            dep_vo_list = [TodoId(UUID(dep_str)) for dep_str in dto.dependencies]
            dependencies_vo = TodoDependencies.from_list(dep_vo_list)

        # 2) Factory でドメインエンティティ生成
        return TodoFactory.create(
            title=title_vo,
            project_id=project_id,
            description=description_vo,
            dependencies=dependencies_vo,
        )
```

### 7.3 UseCase修正例

```python
# dddpy/usecase/project/add_todo_to_project_usecase.py

from dddpy.usecase.assembler.todo_create_assembler import TodoCreateAssembler

class AddTodoToProjectUseCaseImpl(AddTodoToProjectUseCase):
    def execute(self, project_id: str, dto: AddTodoToProjectDto) -> TodoOutputDto:
        _project_id = ProjectId(UUID(project_id))
        project = self.project_repository.find_by_id(_project_id)

        if project is None:
            raise ProjectNotFoundError()

        # ★ 新しいAssemblerを使用してDTO→Entityに変換
        todo_create_dto = TodoCreateDto(
            title=dto.title,
            description=dto.description,
            dependencies=dto.dependencies,
        )
        todo = TodoCreateAssembler.to_entity(todo_create_dto, project_id)

        # Project に Todo を追加する専用メソッドが必要な場合
        # project.add_todo_entity(todo)
        # または既存のadd_todoメソッドを使用
        
        # 既存実装に合わせる場合
        title = TodoTitle(dto.title)
        description = TodoDescription(dto.description) if dto.description else None
        dependencies = None
        if dto.dependencies:
            dependencies = [TodoId(UUID(dep_id)) for dep_id in dto.dependencies]

        todo = project.add_todo(title, description, dependencies)
        
        self.project_repository.save(project)
        return TodoConverter.to_output_dto(todo)
```
