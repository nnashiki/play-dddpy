┌─────────────┐   publish()                     ┌─────────────┐
│  Domain層   │  (メモリに蓄積)                  │   UseCase   │
│ Project etc │ ───────────────┐              ┌─► executes   │
└─────────────┘                │              │ └─────────────┘
                               │ events       │     ▲
                               ▼              │     │
                         ┌─────────────┐      │  with UnitOfWork
                         │DomainEvents │      │     │
                         └─────────────┘      ▼     │
                                   flush_to_outbox() │
                         ┌───────────────────────────┴────┐
                         │      UnitOfWork (new)          │
                         │  ├─ SQLAlchemy Session         │
                         │  └─ DomainEventPublisher       │
                         │        (events property)       │
                         └──────────────┬─────────────────┘
                                        │ commits same Tx
                                        ▼
                              ┌────────────────┐
                              │ Outboxテーブル │  ◄─ INSERT (Tx内)
                              └────────────────┘

# Unit of Work 直接置換計画書 v5.0

## 🎯 背景・目的

### 現在の課題
現在のシステムは `SessionLocal()` による簡易的なセッション管理を使用していますが、以下の課題があります：

1. **イベント送信の信頼性不足**
   - ドメインイベントが即座に外部システムに送信される
   - 送信失敗時にイベントが失われるリスク
   - ドメイン変更とイベント送信が別トランザクションで不整合の可能性

2. **トランザクション管理の複雑性**
   - 各UseCaseで個別にcommit/rollback処理
   - 複雑な業務処理での一貫性担保が困難

3. **拡張性の限界**
   - 将来のKafka/SNS連携時の基盤不足
   - マイクロサービス化での分散トランザクション対応困難

### 解決策：Outboxパターン + Unit of Work
**Outboxパターン**：ドメイン変更と同一トランザクション内でイベントをデータベースに保存し、後で非同期送信
**Unit of Work**：トランザクション境界を明確化し、Outboxへの書き込みを自動化

### 期待効果
1. **データ整合性保証**：ドメイン変更とイベント保存が同一トランザクション
2. **イベント損失防止**：送信失敗時でもイベントがOutboxに保持
3. **信頼性向上**：At-least-once配信の実現
4. **拡張性確保**：将来の分散システム対応基盤
5. **ドメイン層の純粋化**：送信ロジックとの完全分離

### 実装方針
既存のエンドポイントとAPIを維持したまま、内部実装をUoW+Outboxパターンに置換します。利用者には一切の変更を感じさせず、システムの信頼性と拡張性を大幅に向上させます。

---

## 📋 現状分析（v5.0更新）

### ✅ 実装済み・完了
- `SqlAlchemyUnitOfWork` クラス
- **CreateProjectUseCase**: UoW版に完全置換済み（命名統一済み）
- **AddTodoToProjectUseCase**: UoW版に完全置換済み（命名統一済み）
- **UpdateTodoThroughProjectUseCase**: UoW版に完全置換済み（命名統一済み）
- **DeleteProjectUseCase**: UoW版に完全置換済み（命名統一済み）
- **StartTodoThroughProjectUseCase**: UoW版に完全置換済み（命名統一済み）
- **CompleteTodoThroughProjectUseCase**: UoW版に完全置換済み（命名統一済み）
- **FindProjectsUseCase**: UoW版に完全置換済み（命名統一済み） ⭐ NEW
- Outbox パターンの基盤インフラ
- DI関数 `get_uow()`
- 包括的なユニットテスト（52+テスト） ⭐ 更新
- **TodoUpdatedEvent**: 新規実装完了
- **ProjectDeletedEvent**: 新規実装完了
- **TodoStartedEvent**: 新規実装完了
- **TodoCompletedEvent**: 新規実装完了

### 🎉 フェーズ1完了！
**フェーズ1 (Write操作): 6/6 完了 (100%)**
- ✅ CreateProjectUseCase置換
- ✅ AddTodoToProjectUseCase置換
- ✅ UpdateTodoThroughProjectUseCase置換
- ✅ DeleteProjectUseCase置換
- ✅ StartTodoThroughProjectUseCase置換
- ✅ CompleteTodoThroughProjectUseCase置換

### 🥈 フェーズ2進行中！
**フェーズ2 (Read操作): 1/2 完了 (50%)** ⭐ 進捗更新
- ✅ **FindProjectsUseCase置換（完了）** ⭐ NEW
- 🔄 FindTodoThroughProjectUseCase置換（次のタスク）

---

## 🎯 直接置換戦略

### 基本方針
1. **既存エンドポイントをそのまま使用**：`/projects`, `/projects/{id}/todos` 等
2. **段階的置換**：1つずつ確実に置き換え
3. **完全互換性維持**：APIレスポンス・エラーハンドリング同一
4. **追加機能のみ**：Outboxイベント保存が唯一の追加機能
5. **クリーンな命名**：WithUoWなどの接尾辞は使わず、標準的な命名に統一

### 置換パターン
```
置換前: POST /projects → CreateProjectUseCase → get_session()
置換後: POST /projects → CreateProjectUseCaseImpl → get_uow()
```

---

## 🔧 標準置換手順テンプレート（v5.0確定版）

### 各UseCase置換の8ステップ

```python
# ステップ1: UoW版UseCase実装（命名規則統一）
class XxxUseCase(ABC):  # インターフェース（既存と同名）
    @abstractmethod
    def execute(self, dto: XxxDto) -> XxxOutputDto:
        pass

class XxxUseCaseImpl(XxxUseCase):  # 実装クラス（WithUoWなし）
    def __init__(self, uow: SqlAlchemyUnitOfWork) -> None:
        self.uow = uow

    def execute(self, dto: XxxDto) -> XxxOutputDto:
        result: XxxOutputDto
        with self.uow as uow:
            if uow.session is None:  # Read操作はevent_publisherチェック不要
                raise RuntimeError("UoW was not properly initialized")
            # ビジネスロジック実装
            result = ...
        return result

def new_xxx_usecase(uow: SqlAlchemyUnitOfWork) -> XxxUseCase:
    return XxxUseCaseImpl(uow)

# ステップ2: ユニットテスト実装
class TestXxxUseCase:  # WithUoWなし
    def test_xxx_successfully_xxx(self):
        # 正常ケース + Read操作ではOutbox非作成確認
    def test_xxx_handles_errors_gracefully(self):
        # エラーケース
    def test_xxx_performance_with_large_dataset(self):
        # パフォーマンステスト（Read操作では重要）

# ステップ3: DI関数置換
def get_xxx_usecase(
    uow: SqlAlchemyUnitOfWork = Depends(get_uow),
) -> XxxUseCase:  # インターフェースは同一
    return new_xxx_usecase(uow)

# ステップ4: APIハンドラー更新（Dependency変更のみ）
@app.get('/xxx')  # URLは変更なし
def xxx_endpoint(
    usecase: XxxUseCase = Depends(get_xxx_usecase),  # 型は同一
):
    return usecase.execute(dto)  # 呼び出しも同一

# ステップ5: 既存APIテスト実行（100%パス必須）
# ステップ6: Read操作の場合：Outbox非作成確認テスト実行
# ステップ7: 旧UseCase・DI関数削除
# ステップ8: ファイル名・クラス名の統一
```

---

## 🔧 修正時の重要ポイント（実績ベース）

### 1. 命名規則の統一
```python
❌ 避けるべき命名
- FindProjectsWithUoWUseCase
- FindProjectsWithUoWUseCaseImpl
- TestFindProjectsWithUoWUseCase

✅ 推奨命名
- FindProjectsUseCase (インターフェース)
- FindProjectsUseCaseImpl (実装)
- TestFindProjectsUseCase (テストクラス)
```

### 2. Read操作でのUoWパターン ⭐ NEW
```python
# Read操作では軽量な実装を使用
class FindProjectsUseCaseImpl(FindProjectsUseCase):
    def execute(self) -> list[ProjectOutputDto]:
        result: list[ProjectOutputDto]
        with self.uow as uow:
            # Read操作ではevent_publisherチェック不要
            if uow.session is None:
                raise RuntimeError('UoW was not properly initialized')
            
            # リポジトリ作成・データ取得・DTO変換
            project_repository = new_project_repository(uow.session)
            projects = project_repository.find_all()
            result = [convert_to_dto(project) for project in projects]
        return result
```

### 3. Read操作でのテスト重要項目 ⭐ NEW
```python
# Read操作で特に重要なテスト項目
def test_find_xxx_does_not_create_outbox_entries(self):
    # Read操作はOutboxエントリを作成しないことを確認
    outbox_count_before = get_outbox_count()
    result = usecase.execute()
    outbox_count_after = get_outbox_count()
    assert outbox_count_after == outbox_count_before

def test_find_xxx_performance_with_large_dataset(self):
    # 大量データでの性能確認（Read操作では特に重要）
    create_large_dataset(50)  # 大量データ作成
    start_time = time.time()
    result = usecase.execute()
    execution_time = time.time() - start_time
    assert execution_time < 5.0  # 性能要件
```

### 4. インターフェース継承の徹底
```python
# UoW版は必ず既存インターフェースを継承
class FindProjectsUseCaseImpl(FindProjectsUseCase):  # ✅
    pass

class FindProjectsWithUoWUseCase(ABC):  # ❌ 新しいインターフェース作成は不要
    pass
```

### 5. 中間クラスの削除
```python
❌ 不要な中間クラス
class FindProjectsWithUoWUseCase(FindProjectsUseCase):
    pass
class FindProjectsWithUoWUseCaseImpl(FindProjectsWithUoWUseCase):
    pass

✅ シンプルな構造
class FindProjectsUseCaseImpl(FindProjectsUseCase):
    pass
```

### 6. テストでの想定値確認
```python
# データ構造の実際の値を確認
assert isinstance(result, list)  # ✅ 実際の型
assert len(result) == expected_count  # ✅ 実際の数量

# レスポンス形式の一貫性確認
for project in result:
    assert project.id is not None
    assert isinstance(project.name, str)
    assert isinstance(project.todos, list)
```

---

## 📅 フェーズ別置換計画（v5.0更新版）

### 🏆 フェーズ1：Write操作の置換（完了！）

#### ✅ 1.1 CreateProjectUseCase置換（完了）
- [x] `/projects-with-outbox` エンドポイント削除
- [x] `injection.py`の`get_create_project_usecase()`をUoW版に置換
- [x] `project_api_route_handler.py`の`create_project`関数修正
- [x] `CreateProjectUseCase`（旧版）削除・統一
- [x] 既存APIテスト実行（100%パス確認）
- [x] Outbox保存確認テスト
- [x] 命名統一（WithUoW削除）

#### ✅ 1.2 AddTodoToProjectUseCase置換（完了）
- [x] `AddTodoToProjectUseCaseImpl`実装
- [x] ユニットテスト（成功・失敗・ロールバック・複数Todo・依存関係）
- [x] DI関数置換：`get_add_todo_to_project_usecase()`
- [x] API: `POST /projects/{id}/todos` 置換
- [x] 旧UseCase削除・統一
- [x] 命名統一（WithUoW削除）

#### ✅ 1.3 UpdateTodoThroughProjectUseCase置換（完了）
- [x] `UpdateTodoThroughProjectUseCaseImpl`実装
- [x] `TodoUpdatedEvent`ドメインイベント新規作成
- [x] Projectエンティティでの条件付きイベント発行実装
- [x] ユニットテスト（6テスト：成功・失敗・依存関係・部分更新・複数更新・ロールバック）
- [x] DI関数置換：`get_update_todo_usecase()`
- [x] API: `PUT /projects/{id}/todos/{todo_id}` 置換
- [x] 既存APIテスト実行（正常・エラーケース100%パス確認）
- [x] Outboxイベント保存確認（TodoUpdatedイベント正常保存）
- [x] 命名統一（WithUoW削除）

#### ✅ 1.4 DeleteProjectUseCase置換（完了）
- [x] `DeleteProjectUseCaseImpl`実装
- [x] `ProjectDeletedEvent`ドメインイベント新規作成
- [x] カスケード削除のトランザクション検証
- [x] ユニットテスト（5テスト：成功・失敗・複数削除・データ検証・ロールバック）
- [x] DI関数置換：`get_delete_project_usecase()`
- [x] API: `DELETE /projects/{id}` 置換
- [x] 既存APIテスト実行（正常・エラーケース100%パス確認）
- [x] Outboxイベント保存確認（ProjectDeletedイベント正常保存）
- [x] 命名統一（WithUoW削除）

#### ✅ 1.5 StartTodoThroughProjectUseCase置換（完了）
- [x] `StartTodoThroughProjectUseCaseImpl`実装
- [x] `TodoStartedEvent`ドメインイベント新規作成
- [x] Projectエンティティでのイベント発行実装
- [x] ユニットテスト（8テスト：成功・失敗・依存関係・既開始・複数・データ検証・ロールバック）
- [x] DI関数置換：`get_start_todo_usecase()`
- [x] API: `PATCH /projects/{id}/todos/{todo_id}/start` 置換
- [x] 既存APIテスト実行（正常・エラーケース100%パス確認）
- [x] Outboxイベント保存確認（TodoStartedイベント正常保存）
- [x] 旧テストファイル削除・統一
- [x] 命名統一（WithUoW削除）

#### ✅ 1.6 CompleteTodoThroughProjectUseCase置換（完了）
- [x] `CompleteTodoThroughProjectUseCaseImpl`実装
- [x] `TodoCompletedEvent`ドメインイベント新規作成
- [x] Projectエンティティでのイベント発行実装
- [x] ユニットテスト作成（6テスト：成功・失敗・依存関係・ワークフロー・データ検証・ロールバック）
- [x] DI関数置換：`get_complete_todo_usecase()`
- [x] API: `PATCH /projects/{id}/todos/{todo_id}/complete` 置換
- [x] 旧テストファイル削除・統一
- [x] 命名統一（WithUoW削除）

### 🥈 フェーズ2：Read操作の置換（1.5週間）⭐ 進行中

#### ✅ 2.1 FindProjectsUseCase置換（完了）⭐ NEW
- [x] `FindProjectsUseCaseImpl`UoW版実装（Read専用軽量パターン）
- [x] ユニットテスト（7テスト：空DB・正常取得・Outbox非作成・エラーハンドリング・パフォーマンス・データ一貫性・独立操作）
- [x] DI関数置換：`get_find_projects_usecase()`をUoW版に
- [x] API: `GET /projects` 動作確認（実際のHTTPテスト実行）
- [x] 既存APIとの完全互換性確認
- [x] 大量データ取得時のパフォーマンステスト（50プロジェクト/5秒以内）
- [x] 命名統一（WithUoW削除）

#### 🔄 2.2 FindTodoThroughProjectUseCase置換（次のタスク）
- [ ] `FindTodoThroughProjectUseCaseImpl`UoW版実装
- [ ] ユニットテスト（6テスト予定：正常取得・Todo不存在・Project不存在・Outbox非作成・エラーハンドリング・データ一貫性）
- [ ] DI関数置換：`get_find_todo_usecase()`をUoW版に
- [ ] API: `GET /projects/{id}/todos/{todo_id}` 置換
- [ ] 既存APIテストでの互換性確認
- [ ] 命名統一（WithUoW削除）

### 🥉 フェーズ3：残りのRead操作置換（1週間）

#### 3.1 その他Todo関連UseCase
- [ ] 残りのTodo検索系UseCase置換
- [ ] Read専用操作の軽量化検討

### 🏁 フェーズ4：インフラ整理（2週間）

#### 4.1 旧インフラ削除（1週間）
- [ ] `get_session()`関数削除
- [ ] `get_project_repository()`関数削除（get_find_todo_usecase置換後）
- [ ] Session版UseCase全削除
- [ ] 不要なDI関数削除

#### 4.2 最終検証・文書化（1週間）
- [ ] 全機能統合テスト
- [ ] パフォーマンス検証
- [ ] 運用手順更新

---

## 📊 品質保証戦略（v5.0実績更新）

### テスト要件
1. **互換性テスト**: 既存のAPIテスト100%パス（✅ 7回達成済み）
2. **Outboxテスト**: Write操作でイベント保存確認（✅ 6回達成済み）
3. **Read操作テスト**: Outbox非作成確認（✅ 1回達成済み）⭐ NEW
4. **トランザクションテスト**: 失敗時の完全ロールバック（✅ 6回達成済み）
5. **パフォーマンステスト**: レスポンス時間劣化<10%（✅ 問題なし）

### 実績のある検証チェックリスト
- [x] APIレスポンス形式：既存と完全同一（7回確認）⭐ 更新
- [x] エラーレスポンス：既存と完全同一（7回確認）⭐ 更新
- [x] HTTPステータスコード：既存と完全同一（7回確認）⭐ 更新
- [x] バリデーション：既存と完全同一（7回確認）⭐ 更新
- [x] **新機能**: Outboxイベント正常保存（6回確認）
- [x] **新機能**: エラー時の完全ロールバック（6回確認）
- [x] **新機能**: Read操作でのOutbox非作成（1回確認）⭐ NEW
- [x] **命名統一**: WithUoW接尾辞の完全削除（7回確認）⭐ 更新

### 新規実装項目の累積
- [x] **TodoUpdatedEvent**: 条件付きイベント発行の実装
- [x] **ProjectDeletedEvent**: プロジェクト削除イベントの実装
- [x] **TodoStartedEvent**: Todo開始イベントの実装
- [x] **TodoCompletedEvent**: Todo完了イベントの実装
- [x] **部分更新対応**: title/description/dependenciesの個別更新
- [x] **更新追跡**: 実際に変更があった場合のみイベント発行
- [x] **依存関係検証**: 循環依存・存在チェックの維持
- [x] **旧テストファイル削除**: 互換性のない旧テストの適切な除去
- [x] **ワークフロー整合性**: Todo完了前のstart状態要求の実装
- [x] **Read操作UoWパターン**: 軽量で一貫性のあるRead実装 ⭐ NEW

### 監視項目
1. **API正常性**: 各エンドポイントのレスポンス時間
2. **Outbox健全性**: イベント保存率、未送信イベント数
3. **システム負荷**: CPU・メモリ・DB接続数
4. **Read性能**: 大量データ取得時のレスポンス時間 ⭐ NEW

---

## ⚠️ リスク管理（v5.0実績反映）

### 技術リスク・対策
| リスク               | 対策                               | 実績                       |
| -------------------- | ---------------------------------- | -------------------------- |
| API互換性破綻        | 置換前後でレスポンス形式比較テスト | ✅ 7回成功 ⭐ 更新           |
| パフォーマンス劣化   | 各置換後にベンチマーク実行         | ✅ 劣化なし                 |
| トランザクション障害 | 詳細なエラーログ・監視             | ✅ 適切なロールバック確認   |
| Outboxテーブル肥大化 | 容量監視・削除バッチ準備           | 🔄 要継続監視               |
| 命名不統一           | 命名規則の徹底とレビュー           | ✅ 統一完了                 |
| ドメインイベント設計 | 条件付き発行とペイロード設計       | ✅ 4種イベント成功          |
| テスト期待値ずれ     | 実際のイベント数を正確に把握       | ✅ 適切な修正完了           |
| ワークフロー依存関係 | Todo状態遷移の前提条件チェック     | ✅ Complete実装で確認       |
| Read操作の性能劣化   | 大量データでの性能テスト実行       | ✅ 50件/5秒以内で確認 ⭐ NEW |

### 緊急時対応
1. **即座のロールバック**: Git revert で前バージョンに戻す
2. **部分的切り戻し**: 問題のあるUseCaseのみ旧版に戻す
3. **監視アラート**: 異常検知時の自動通知

---

## 🎯 成功基準（v5.0更新版）

### ✅ フェーズ1完了基準（達成済み！）
- [x] CreateProject・AddTodoでOutboxイベント保存率100%
- [x] UpdateTodoでOutboxイベント保存率100%
- [x] DeleteProjectでOutboxイベント保存率100%
- [x] StartTodoでOutboxイベント保存率100%
- [x] CompleteTodoでOutboxイベント保存率100%
- [x] 既存APIテスト100%パス維持（6回確認）
- [x] レスポンス時間劣化<10%
- [x] エラー時の不整合0件
- [x] 命名規則の完全統一
- [x] 全Write操作の置換完了（6/6達成）

### ✅ フェーズ2.1完了基準（達成済み！）⭐ NEW
- [x] FindProjectsでUoWパターン適用100%
- [x] Read操作でのOutbox非作成確認100%
- [x] 大量データ取得でのパフォーマンス要件達成（50件/5秒以内）
- [x] 既存API完全互換性維持（GET /projectsで確認）
- [x] ユニットテスト100%パス（7テスト）
- [x] 実際のHTTPリクエストでの動作確認

### 🔄 フェーズ2.2完了基準（次のタスク）
- [ ] FindTodoThroughProjectでUoWパターン適用100%
- [ ] Todo検索でのOutbox非作成確認100%
- [ ] 既存API完全互換性維持（GET /projects/{id}/todos/{todo_id}で確認）
- [ ] ユニットテスト100%パス（6テスト予定）
- [ ] エラーハンドリングの既存同等品質維持

### 最終完了基準
- [ ] 全UseCase がUoW版に置換完了
- [ ] 旧Session基盤完全削除
- [ ] 統合テスト100%パス
- [ ] WithUoW等の不適切な命名の完全排除

---

## 🎉 フェーズ別完了の重要な成果

### フェーズ1完了の技術的価値
1. **データ整合性の確立**: 全Write操作でドメイン変更とイベント保存が同一トランザクション
2. **イベント損失防止**: Outboxパターンによりイベントが確実に保持
3. **システム信頼性向上**: At-least-once配信の基盤完成
4. **拡張性基盤構築**: マイクロサービス・分散システム対応の土台完成
5. **ドメイン層の純粋化**: 外部システム依存の完全排除

### フェーズ2.1完了の技術的価値 ⭐ NEW
1. **アーキテクチャ統一**: Read/Write操作で一貫したUoWパターン
2. **トランザクション境界明確化**: Read操作でも明示的なスコープ管理
3. **性能要件達成**: 大量データでも安定したレスポンス時間
4. **拡張性確保**: 将来のキャッシュ・分散読み込み対応基盤
5. **保守性向上**: 統一されたパターンで開発・運用効率向上

### 実装された7つのドメインイベント
- **ProjectCreated**: プロジェクト作成時
- **TodoCreated**: Todo作成時  
- **TodoAddedToProject**: TodoのProject追加時
- **TodoUpdated**: Todo更新時（条件付き発行）
- **ProjectDeleted**: プロジェクト削除時
- **TodoStarted**: Todo開始時
- **TodoCompleted**: Todo完了時

### 品質指標
- **API互換性**: 100%維持（既存利用者への影響ゼロ）
- **テストカバレッジ**: 52+テストで網羅 ⭐ 更新
- **パフォーマンス**: Write/Read共に劣化なし
- **エラーハンドリング**: 既存と同等の品質維持

---

## 📝 次のアクション：フェーズ2.2開始

### フェーズ2.2の準備
フェーズ2.1の成功により、以下が確立されました：
- **Read操作用UoWパターン**: 軽量で効率的な実装方式
- **性能テスト戦略**: 大量データでの実証済み品質保証
- **API互換性保証**: 実際のHTTPリクエストでの検証方法
- **Outbox非作成確認**: