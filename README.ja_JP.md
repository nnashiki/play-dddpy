# Python DDD & Onion-Architecture Example and Techniques

[![A workflow to run test](https://github.com/iktakahiro/dddpy/actions/workflows/test.yml/badge.svg)](https://github.com/iktakahiro/dddpy/actions/workflows/test.yml)

[English](README.md) | 日本語

**注意**: このリポジトリは「PythonのWebアプリケーションでDDDアーキテクチャを実装する方法」を説明するためのサンプルです。参考として使用する場合は、本番環境にデプロイする前に認証とセキュリティの実装を追加してください。

**🚀 新機能**: Project Aggregate を導入し、複数のTodoを管理する新しいアーキテクチャを実装しました。依存関係管理がより堅牢になり、DDDの集約パターンを適用しています。

* DeepWiki powered by Devin: <https://deepwiki.com/iktakahiro/dddpy>
* ブログ記事: [Python DDD オニオンアーキテクチャ](https://iktakahiro.dev/python-ddd-onion-architecture)

## 技術スタック

* [FastAPI](https://fastapi.tiangolo.com/)
* [SQLAlchemy](https://www.sqlalchemy.org/)
  * [SQLite](https://www.sqlite.org/index.html)
* [uv](https://github.com/astral-sh/uv)
* [Docker](https://www.docker.com/)

## プロジェクトのセットアップ

1. uvを使用して依存関係をインストールします：

```bash
make install
```

2. Webアプリケーションを実行します：

```bash
make dev
```

## ソフトウェアアーキテクチャ

このリポジトリのソフトウェアアーキテクチャは、[オニオン・アーキテクチャ](https://jeffreypalermo.com/2008/07/the-onion-architecture-part-1/)に基づいています。

オニオン・アーキテクチャを実践するためのディレクトリ構造に正解はありませんが、このリポジトリでは次のようなディレクトリ構造を採用しています：

```tree
├── main.py
├── dddpy
│   ├── domain
│   │   └── todo
│   │       ├── entities
│   │       │   └── todo.py
│   │       ├── value_objects
│   │       │   ├── todo_title.py
│   │       │   ├── todo_description.py
│   │       │   ├── todo_id.py
│   │       │   └── todo_status.py
│   │       ├── repositories
│   │       │   └── todo_repository.py
│   │       └── exceptions
│   ├── infrastructure
│   │   ├── di
│   │   │   └── injection.py
│   │   └── sqlite
│   │       ├── database.py
│   │       └── todo
│   │           ├── todo_repository.py
│   │           └── todo_dto.py
│   ├── presentation
│   │   └── api
│   │       └── todo
│   │           ├── handlers
│   │           │   └── todo_api_route_handler.py
│   │           ├── schemas
│   │           │   └── todo_schema.py
│   │           └── error_messages
│   │               └── todo_error_message.py
│   └── usecase
│       └── todo
│           ├── create_todo_usecase.py
│           ├── update_todo_usecase.py
│           ├── start_todo_usecase.py
│           ├── find_todos_usecase.py
│           ├── find_todo_by_id_usecase.py
│           ├── complete_todo_usecase.py
│           └── delete_todo_usecase.py
└── tests
```

### ドメイン層

ドメイン層には、コアとなるビジネスロジックとルールが含まれています。このプロジェクトでは **Project Aggregate パターン** を採用し、より堅牢な依存関係管理を実現しています。

主に以下の要素で構成されています：

1. **Project Aggregate Root** - 新機能
2. **Todo Entity** - Project内で管理される
3. 値オブジェクト
4. リポジトリインターフェース

#### 🆕 Project Aggregate Root

`Project` は複数の `Todo` を内包し、それらの依存関係を管理する集約ルートです：

```python
class Project:
    """Project aggregate root that manages multiple Todos and their dependencies."""
    
    def add_todo(
        self,
        title: TodoTitle,
        description: Optional[TodoDescription] = None,
        dependencies: Optional[List[TodoId]] = None,
    ) -> Todo:
        """Add a new Todo to the project with dependency validation"""
        # 依存関係の存在確認
        if dependencies:
            self._validate_dependencies_exist(dependencies)
        
        # Todoを作成
        todo = Todo.create(title, self.id, description, deps)
        
        # 循環依存をチェック
        if dependencies:
            self._validate_no_circular_dependency(todo.id, dependencies)
        
        self._todos[todo.id] = todo
        return todo
    
    def start_todo(self, todo_id: TodoId) -> None:
        """Start a Todo after validating all dependencies are completed"""
        todo = self.get_todo(todo_id)
        
        if not self._can_start_todo(todo):
            raise TodoDependencyNotCompletedError()
        
        todo.start()
```

**Project Aggregate の主な特徴：**

* **整合性保証**: 依存関係の検証（循環依存、存在確認、完了状態チェック）を集約内で実行
* **カプセル化**: Todo の依存関係操作メソッドを非公開化し、Project 経由でのみアクセス可能
* **トランザクション境界**: Project 全体を単一のトランザクションで永続化
* **ビジネスルール実装**: 「依存先が完了していない Todo は開始できない」などのルールを集約内で実装

このプロジェクトでの各コンポーネントの実装は以下の通りです：

#### 1. Todo エンティティ（Project内で管理）

`Todo` エンティティは `Project` 集約内で管理され、project_id を必須フィールドとして持ちます：

```python
class Todo:
    def __init__(
        self,
        id: TodoId,
        title: TodoTitle,
        project_id: ProjectId,  # プロジェクトIDが必須
        description: Optional[TodoDescription] = None,
        status: TodoStatus = TodoStatus.NOT_STARTED,
        # ...
    ):
        self._id = id
        self._title = title
        self._project_id = project_id
        # ...
    
    # 依存関係操作メソッドは非公開化（Project経由でのみ使用）
    def _add_dependency(self, dep_id: TodoId) -> None:
        """Add a dependency to this Todo (for internal use by Project)"""
        # ...
```

**主な変更点：**

* **project_id フィールド**: どのProjectに属するかを明確化
* **依存関係メソッドの非公開化**: `_add_dependency`, `_remove_dependency`, `_set_dependencies` はProject内でのみ使用
* **整合性保証の委譲**: 循環依存や存在確認などの検証はProjectが担当

エンティティの主な特徴：

* 一意の識別子（`id`）を持つ
* 状態を変更できる（例: `update_title`, `update_description`, `start`, `complete` メソッド）
* 識別子によって同一性が決定される（`__eq__`メソッドの実装）
* ファクトリメソッド（例: `create`）を通じて生成されることがある

このプロジェクトでは、インスタンスの同一性を `id` のみによって判断するため、`__eq__` メソッドを以下のように実装しています。

```python
def __eq__(self, obj: object) -> bool:
    if isinstance(obj, Todo):
        return self.id == obj.id
    return False
```

この実装のポイント：

* 同一性は識別子（`id`）のみによって判断される
* `isinstance`チェックによる型安全性が確保されている

#### 2. 値オブジェクト

値オブジェクトは識別子を持たない不変のドメインモデルです。このプロジェクトでは、以下のような値オブジェクトを実装しています：

```python
@dataclass(frozen=True)
class TodoTitle:
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError('Title is required')
        if len(self.value) > 100:
            raise ValueError('Title must be 100 characters or less')
```

値オブジェクトの主な特徴：

* `@dataclass(frozen=True)`による不変性の保証
* 値の検証ロジックを含む（`__post_init__`）
* 識別子を持たない
* すべての値の内容によって同一性が決定される

#### 3. リポジトリインターフェース

リポジトリはエンティティの永続化を担当する抽象化レイヤーです。このプロジェクトでは`TodoRepository`インターフェースを次のように定義しています：

```python
class TodoRepository(ABC):
    @abstractmethod
    def save(self, todo: Todo) -> None:
        """Save a Todo"""

    @abstractmethod
    def find_by_id(self, todo_id: TodoId) -> Optional[Todo]:
        """Find a Todo by ID"""

    @abstractmethod
    def find_all(self) -> List[Todo]:
        """Get all Todos"""

    @abstractmethod
    def delete(self, todo_id: TodoId) -> None:
        """Delete a Todo by ID"""
```

リポジトリの主な特徴：

* エンティティの永続化を抽象化する

### インフラ層

インフラ層はドメイン層で定義されたインターフェースを実装します。主に以下の要素で構成されています：

1. データベース設定
2. リポジトリの実装
3. 外部サービスとの統合
4. 依存性注入（DI）の設定

#### 1. リポジトリの実装

リポジトリの実装は、次のように行います：

```python
class TodoRepositoryImpl(TodoRepository):
    """SQLite implementation of Todo repository interface."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session."""
        self.session = session

    def find_by_id(self, todo_id: TodoId) -> Optional[Todo]:
        """Find a Todo by its ID."""
        try:
            row = self.session.query(TodoDTO).filter_by(id=todo_id.value).one()
        except NoResultFound:
            return None

        return row.to_entity()

    def save(self, todo: Todo) -> None:
        """Save a new Todo item."""
        todo_dto = TodoDTO.from_entity(todo)
        try:
            existing_todo = (
                self.session.query(TodoDTO).filter_by(id=todo.id.value).one()
            )
        except NoResultFound:
            self.session.add(todo_dto)

        else:
            existing_todo.title = todo_dto.title
            existing_todo.description = todo_dto.description
            existing_todo.status = todo_dto.status
            existing_todo.updated_at = todo_dto.updated_at
            existing_todo.completed_at = todo_dto.completed_at
```

リポジトリインターフェースとは異なり、インフラ層の実装コードには、特定の技術（この例ではSQLite）に依存する詳細が含まれていても問題ありません。むしろ、抽象的なインターフェース定義にとらわれすぎず、具体的な技術名をディレクトリ名（例: `sqlite`）やクラス名に含めることで、その実装がどの技術に基づいているかを明確にすることが推奨されます。

#### 2. Data Transfer Object (DTO)

オニオンアーキテクチャでは、内側のレイヤー（ドメイン層）は外側のレイヤー（インフラ層、プレゼンテーション層）に依存しません。そのため、レイヤー間でデータをやり取りする際に、特定のレイヤーの詳細（例えば、インフラ層のデータベースモデル）が他のレイヤーに漏れ出ないように、オブジェクトの変換が必要になることがあります。この変換の役割を担うのがData Transfer Object（DTO）です。DTOは、レイヤー間でデータを転送するために使用されるシンプルなオブジェクトです。

`TodoDTO` クラスの例を以下に示します。これは SQLAlchemy のモデル（`Base` を継承）であり、ドメインエンティティ (`Todo`) との間で相互変換を行うメソッド (`to_entity`, `from_entity`) を持ちます。

```python
class TodoDTO(Base):
    """Data Transfer Object for Todo entity in SQLite database."""

    __tablename__ = 'todo'
    id: Mapped[UUID] = mapped_column(primary_key=True, autoincrement=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(1000), nullable=True)
    status: Mapped[str] = mapped_column(index=True, nullable=False)
    created_at: Mapped[int] = mapped_column(index=True, nullable=False)
    updated_at: Mapped[int] = mapped_column(index=True, nullable=False)
    completed_at: Mapped[int] = mapped_column(index=True, nullable=True)

    def to_entity(self) -> Todo:
        """Convert DTO to domain entity."""
        return Todo(
            TodoId(self.id),
            TodoTitle(self.title),
            TodoDescription(self.description),
            TodoStatus(self.status),
            datetime.fromtimestamp(self.created_at / 1000, tz=timezone.utc),
            datetime.fromtimestamp(self.updated_at / 1000, tz=timezone.utc),
            datetime.fromtimestamp(self.completed_at / 1000, tz=timezone.utc)
            if self.completed_at
            else None,
        )

    @staticmethod
    def from_entity(todo: Todo) -> 'TodoDTO':
        """Convert domain entity to DTO."""
        return TodoDTO(
            id=todo.id.value,
            title=todo.title.value,
            description=todo.description.value if todo.description else None,
            status=todo.status.value,
            created_at=int(todo.created_at.timestamp() * 1000),
            updated_at=int(todo.updated_at.timestamp() * 1000),
            completed_at=int(todo.completed_at.timestamp() * 1000)
            if todo.completed_at
            else None,
        )
```

データベースから取得した `TodoDTO` オブジェクト（SQLAlchemyに依存）を、ドメイン層の `Todo` エンティティに変換してからユースケース層に返すことで、ユースケース層がインフラストラクチャ層の詳細に依存することを防ぎます。これにより、リポジトリインターフェースで定義された戻り値の型（`Todo` エンティティ）との整合性も保たれます。

### ユースケース層

ユースケース層には、アプリケーション固有のビジネスルールが含まれています。主に以下の要素で構成されています：

1. ユースケースの実装
2. ユースケースに関係するエラーハンドリング

このプロジェクトでは、「1つのユースケースに1つのパブリックメソッド」というルールを採用し、各ユースケースを単一の`execute`メソッドを持つ独立したクラスとして実装しています。実装例は以下の通りです：

#### 1. ユースケースインターフェースと実装

各ユースケースは以下の構造に従います：

```python
class CreateTodoUseCase:
    """CreateTodoUseCase defines a use case interface for creating a new Todo."""

    @abstractmethod
    def execute(
        self, title: TodoTitle, description: Optional[TodoDescription] = None
    ) -> Todo:
        """execute creates a new Todo."""


class CreateTodoUseCaseImpl(CreateTodoUseCase):
    """CreateTodoUseCaseImpl implements the use case for creating a new Todo."""

    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    def execute(
        self, title: TodoTitle, description: Optional[TodoDescription] = None
    ) -> Todo:
        """execute creates a new Todo."""
        todo = Todo.create(title=title, description=description)
        self.todo_repository.save(todo)
        return todo
```

ユースケースの主な特徴：

* ユースケースごとに1つのクラスを用意
* 単一責任の原則に従う設計

#### 2. エラーハンドリング

ユースケースはドメイン固有のエラーを処理します：

```python
class StartTodoUseCaseImpl(StartTodoUseCase):
    # ... __init__ ...

    def execute(self, todo_id: TodoId) -> Todo:
        todo = self.todo_repository.find_by_id(todo_id)

        if todo is None:
            raise TodoNotFoundError

        if todo.is_completed:
            raise TodoAlreadyCompletedError

        if todo.status == TodoStatus.IN_PROGRESS:
            raise TodoAlreadyStartedError

        todo.start()
        self.todo_repository.save(todo)
        return todo
```

### プレゼンテーション層

プレゼンテーション層はHTTPリクエストとレスポンスを処理します。主に以下の要素で構成されています：

1. FastAPIルートハンドラ
2. リクエスト/レスポンスモデル
3. 入力検証ロジック

ハンドラは`presentation/api`ディレクトリに配置され、アプリケーションのAPI層を形成します。各ドメイン（例：`todo`）は独自のハンドラ、スキーマ、エラーメッセージ定義を持っています。

## 起動方法

1. VSCodeでこのリポジトリをクローンして開きます
2. リモートコンテナを起動します
3. Dockerコンテナのターミナルで`make dev`を実行します
4. APIドキュメントにアクセスします：[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

![OpenAPI Doc](./screenshots/openapi_doc.png)

### RESTful APIのサンプルリクエスト

#### 🆕 Project API（新機能）

* 新しいProjectを作成する：

```bash
curl --location --request POST 'localhost:8000/projects' \
--header 'Content-Type: application/json' \
--data-raw '{
    "name": "My Todo Project",
    "description": "A project to manage my todos"
}'
```

* POSTリクエストのレスポンス：

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "My Todo Project",
    "description": "A project to manage my todos",
    "todos": [],
    "created_at": "2025-05-26T10:30:00Z",
    "updated_at": "2025-05-26T10:30:00Z"
}
```

* ProjectにTodoを追加する（依存関係あり）：

```bash
curl --location --request POST 'localhost:8000/projects/550e8400-e29b-41d4-a716-446655440000/todos' \
--header 'Content-Type: application/json' \
--data-raw '{
    "title": "Setup development environment",
    "description": "Install dependencies and configure IDE",
    "dependencies": ["other-todo-id-here"]
}'
```

* すべてのProjectを取得する：

```bash
curl --location --request GET 'localhost:8000/projects'
```

#### 既存のTodo API（非推奨）

* 新しいTodoを作成する：

```bash
curl --location --request POST 'localhost:8000/todos' \
--header 'Content-Type: application/json' \
--data-raw '{
    "title": "Implement DDD architecture",
    "description": "Create a sample application using DDD principles"
}'
```

* POSTリクエストのレスポンス：

```json
{
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Implement DDD architecture",
    "description": "Create a sample application using DDD principles",
    "status": "not_started",
    "created_at": 1614007224642,
    "updated_at": 1614007224642
}
```

* Todoを取得する：

```bash
curl --location --request GET 'localhost:8000/todos'
```

* GETリクエストのレスポンス：

```json
[
    {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "title": "Implement DDD architecture",
        "description": "Create a sample application using DDD principles",
        "status": "not_started",
    "created_at": 1614006055213,
    "updated_at": 1614006055213
    }
]
```

## 開発

### テストの実行

```bash
make test
```

### コードの品質について

このプロジェクトでは、コード品質を維持するために以下のツールを使用しています：

* [mypy](http://mypy-lang.org/) - 静的型チェック
* [ruff](https://github.com/astral-sh/ruff) - Linter と Formatter
* [pytest](https://docs.pytest.org/) - テスト

### Docker開発環境

このプロジェクトには、Dockerベースの開発環境用の`.devcontainer`設定が含まれています。これにより、異なるマシン間で一貫した開発環境を確保できます。

## ライセンス

このプロジェクトはMITライセンスのもとで公開されています。詳細は[LICENSE](LICENSE)ファイルを参照してください。
