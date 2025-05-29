# Assemblerパターンの実装方針

## 概要

play-dddpy プロジェクトでは、DTO ↔ ドメインエンティティの変換を一元的に管理するため、**Assemblerパターン**を採用しています。

## 設計思想

### 責務の明確化
- **ドメイン層** は変換ロジックを知る必要がない
- **Assembler** が変換責任を一手に引き受ける
- レイヤー分離が明確になる

### 依存方向の一貫性
- DTO → ドメイン の変換
- ドメイン → DTO の変換
- いずれも、Assembler だけがドメインとDTOの両方に依存

## 実装構成

### ディレクトリ構造
```
dddpy/
├── presentation/
│   ├── assembler/
│   │   ├── __init__.py
│   │   └── project_todo_assembler.py
│   └── ...
└── ...
```

### ProjectTodoAssembler の責務

| 変換方向 | メソッド | 説明 |
|---------|---------|------|
| ドメイン → DTO | `to_output_dto()` | エンティティ Todo から API 出力用の TodoOutputDto を生成 |
| DTO → ドメイン | `from_dto()` | DTO を受け取り、ドメインエンティティ Todo を生成（主にテストや再構築用） |

### 実装例

```python
class ProjectTodoAssembler:
    """TodoエンティティとDTO間の変換責務を担う Assembler"""

    @staticmethod
    def to_output_dto(todo: Todo) -> TodoOutputDto:
        return TodoOutputDto(
            id=str(todo.id.value),
            title=todo.title.value,
            description=todo.description.value if todo.description else None,
            status=todo.status.value,
            dependencies=[str(dep_id.value) for dep_id in todo.dependencies.values],
            created_at=todo.created_at,
            updated_at=todo.updated_at,
            completed_at=todo.completed_at,
        )

    @staticmethod
    def from_dto(dto: TodoOutputDto, project_id: str) -> Todo:
        return Todo(
            id=TodoId(UUID(dto.id)),
            title=TodoTitle(dto.title),
            project_id=ProjectId(UUID(project_id)),
            description=TodoDescription(dto.description) if dto.description else None,
            status=TodoStatus(dto.status),
            dependencies=TodoDependencies.from_list([
                TodoId(UUID(dep_id)) for dep_id in dto.dependencies
            ]),
            clock=SystemClock(),
            created_at=dto.created_at,
            updated_at=dto.updated_at,
            completed_at=dto.completed_at,
        )
```

## なぜこの構成にするのか

### 利点

| 観点 | 説明 |
|------|------|
| **責務の明確化** | ドメイン層は変換を知らず、Assemblerが変換責任を一手に引き受けることでレイヤー分離が明確になる |
| **依存方向の一貫性** | DTO → ドメイン／ドメイン → DTO いずれも、Assembler だけがドメインとDTOの両方に依存する |
| **再利用性の向上** | UseCase やテストなど、どこからでも共通の変換を呼び出せる（重複実装が不要） |
| **テスト容易性** | Assembler 単体でのテストが可能。ドメインやDTOの妥当性検証にも使える |
| **拡張性** | 例えば、依存Todoのタイトルなど追加情報が必要になっても、Assemblerで拡張できる |

### 使用例（from_dto）

ユースケースやテストコードで再構築する場面で活用：

```python
todo = ProjectTodoAssembler.from_dto(todo_dto, project_id="123e...")
project.add_existing_todo(todo)
```

※ `add_existing_todo()` は既存のTodoを再登録するためのドメインメソッドとして別途設計可能。

### 今後の拡張

- `ProjectAssembler` や `ProjectSummaryAssembler` などの導入も同様の方式で行うと統一感が保てます
- `from_dto()` を使って **イベントソーシング** や **永続化レイヤ再構築**の足がかりにもなります

## 実装状況

### 適用済みファイル

以下のユースケースで、従来の手動変換からAssemblerを使用する形に更新済み：

- `FindTodoThroughProjectUseCase` - Todoの検索
- `StartTodoThroughProjectUseCase` - Todoの開始
- `CompleteTodoThroughProjectUseCase` - Todoの完了
- `UpdateTodoThroughProjectUseCase` - Todoの更新
- `AddTodoToProjectUseCase` - プロジェクトへのTodo追加
- `FindProjectsUseCase` - プロジェクト一覧取得（内部のTodo変換）

### 変更前と変更後の比較

**変更前（手動変換）：**
```python
return TodoOutputDto(
    id=str(todo.id.value),
    title=todo.title.value,
    description=todo.description.value if todo.description else None,
    status=todo.status.value,
    dependencies=[str(dep_id.value) for dep_id in todo.dependencies.values],
    created_at=todo.created_at,
    updated_at=todo.updated_at,
    completed_at=todo.completed_at,
)
```

**変更後（Assembler使用）：**
```python
return ProjectTodoAssembler.to_output_dto(todo)
```

## まとめ

Assemblerパターンの採用により、以下を実現：

- **レイヤ分離**の徹底
- **責務の明確化**
- **変更耐性**の向上  
- **再利用性**の確保
- **テスト容易性**の向上
- **コードの簡潔性**向上（10行以上の変換ロジックが1行に）

これにより、保守性が高く拡張しやすいアーキテクチャが実現されています。
