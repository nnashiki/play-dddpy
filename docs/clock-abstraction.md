# Clock 抽象化の導入

## 概要

このプロジェクトでは、DDDの原則に従って純粋なドメイン層を保つため、`datetime.now()` のような副作用を持つ操作を Clock 抽象により置き換えました。

## 変更内容

### 1. Clock インターフェースの定義

```python
# dddpy/domain/shared/clock.py
from abc import ABC, abstractmethod
from datetime import datetime


class Clock(ABC):
    """時間を取得するための抽象インターフェース"""
    
    @abstractmethod
    def now(self) -> datetime:
        pass


class SystemClock(Clock):
    """現在時刻を返す本番用の Clock 実装"""

    def now(self) -> datetime:
        return datetime.now()


class FixedClock(Clock):
    """固定時刻を返すテスト用の Clock 実装"""
    
    def __init__(self, fixed_time: datetime):
        self._fixed_time = fixed_time

    def now(self) -> datetime:
        return self._fixed_time
```

### 2. エンティティでの使用

#### Project エンティティ

```python
class Project:
    def __init__(
        self,
        id: ProjectId,
        name: ProjectName,
        description: Optional[ProjectDescription] = None,
        todos: Optional[Dict[TodoId, Todo]] = None,
        clock: Optional[Clock] = None,  # Clock を注入可能に
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        self._clock = clock or SystemClock()  # デフォルトで SystemClock
        self._created_at = created_at or self._clock.now()  # Clock を使用
        self._updated_at = updated_at or self._clock.now()

    def update_name(self, new_name: ProjectName) -> None:
        self._name = new_name
        self._updated_at = self._clock.now()  # datetime.now() ではなく Clock を使用
```

#### Todo エンティティ

```python
class Todo:
    def __init__(
        self,
        id: TodoId,
        title: TodoTitle,
        project_id: 'ProjectId',
        clock: Optional[Clock] = None,  # Clock を注入可能に
        # ... 他のパラメータ
    ):
        self._clock = clock or SystemClock()
        self._created_at = created_at or self._clock.now()
        self._updated_at = updated_at or self._clock.now()

    def complete(self) -> None:
        self._status = TodoStatus.COMPLETED
        self._completed_at = self._clock.now()  # Clock を使用
        self._updated_at = self._completed_at
```

### 3. インフラ層での Clock 注入

```python
# infrastructure/sqlite/project/project_model.py
def to_entity(self) -> Project:
    return Project.from_persistence(
        ProjectId(self.id),
        self.name,
        self.description,
        {},
        datetime.fromtimestamp(self.created_at / 1000, tz=timezone.utc),
        datetime.fromtimestamp(self.updated_at / 1000, tz=timezone.utc),
        SystemClock(),  # 本番環境では SystemClock を注入
    )
```

## 利点

### 1. テストの再現性

固定時刻を使用することで、時刻に依存するテストが安定します：

```python
def test_project_with_fixed_clock():
    fixed_time = datetime(2023, 1, 1, 12, 0, 0)
    clock = FixedClock(fixed_time)
    
    project = Project(
        id=ProjectId.generate(),
        name=ProjectName('Test Project'),
        clock=clock  # 固定時刻を注入
    )
    
    # 全てのタイムスタンプが予測可能
    assert project.created_at == fixed_time
    assert project.updated_at == fixed_time
```

### 2. ドメインの純粋性

- ドメインエンティティは外部システムの時刻に直接依存しない
- 副作用のない純粋な関数として動作
- DDDの原則に従った設計

### 3. 依存性注入

- テスト時には `FixedClock` を注入
- 本番時には `SystemClock` を注入
- 必要に応じて他の Clock 実装（例：タイムゾーン対応）も追加可能

## 使用例

### テストでの使用

```python
from dddpy.domain.shared.clock import FixedClock

def test_todo_completion_timing():
    # 固定時刻を設定
    completion_time = datetime(2023, 6, 15, 14, 30, 45)
    clock = FixedClock(completion_time)
    
    # エンティティに固定時刻を注入
    project = Project(
        id=ProjectId.generate(),
        name=ProjectName('Test Project'),
        clock=clock
    )
    
    # 操作を実行
    todo = project.add_todo(TodoTitle('Test Todo'))
    project.start_todo_by_id(todo.id)
    project.complete_todo_by_id(todo.id)
    
    # 時刻が予測可能であることを検証
    completed_todo = project.get_todo(todo.id)
    assert completed_todo.completed_at == completion_time
```

### カスタム Clock 実装

```python
class UTCClock(Clock):
    """UTC時刻を返すClock実装"""
    
    def now(self) -> datetime:
        return datetime.now(timezone.utc)
```

## まとめ

Clock 抽象化により以下が実現されました：

1. **テストの安定性**: 固定時刻によるテストの再現性
2. **ドメインの純粋性**: 副作用のない純粋なドメインロジック
3. **柔軟性**: 異なる時刻実装の注入が可能
4. **DDD準拠**: DDDの原則に従った設計

この変更により、ドメイン層の品質が向上し、より信頼性の高いテストが可能になりました。
