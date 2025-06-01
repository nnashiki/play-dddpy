

# ドメインイベント (Domain Events)

本ドキュメントでは、ドメイン駆動設計 (DDD) におけるドメインイベントの設計・配置について議論した内容をまとめています。

## 1. ドメインイベントとは

- **ドメインイベント** はドメインモデル内部で発生した重要な状態変化やビジネスルールの達成を表すオブジェクト。  
  例: `TodoCreatedEvent`, `UserRegisteredEvent` など。
- イベント自体は副作用を持たず、単に「何が起きたか」を伝搬するためのデータキャリア。
- 同期処理／非同期処理どちらにも対応可能だが、本プロジェクトでは同期処理を前提とする。

## 2. ドメインイベント発行 (Publishing)

- **エンティティや集約ルート (Aggregate Root) 内部**で発行する。  
- メソッド内でビジネスロジックを実行した直後に、イベントを「バッファ (例: `self.events`)」へ追加する。
- 例:
  ```python
  class Todo:
      def __init__(self, title: str):
          self.title = title
          self.events = []

      def create(self):
          # ビジネスロジック
          self.events.append(TodoCreatedEvent(self.id, self.title))
  ```
- ポイント:
  - イベント発行時点ではまだ永続化せず、単に発生事象を蓄積する。
  - 発行側では副作用を直接呼ばず、後続のサービス層でまとめて処理する。

## 3. ドメインイベント取得 (Dispatching)

- **アプリケーションサービス層**で集約の操作・永続化後に、発行済みイベントを取り出してハンドラーに渡す。
- 例:
  ```python
  class CreateTodoService:
      def __init__(self, todo_repo, event_dispatcher):
          self.todo_repo = todo_repo
          self.event_dispatcher = event_dispatcher

      def execute(self, command):
          todo = Todo(command.title)
          todo.create()
          self.todo_repo.save(todo)

          # 発行されたイベントを全てディスパッチ
          for event in todo.events:
              self.event_dispatcher.dispatch(event)
  ```
- ポイント:
  - データベーストランザクションをコミットした後、または同一トランザクション内で連携して処理する。
  - トランザクション境界を意識し、整合性を保つ。

## 4. ドメインイベント処理 (Handling)

- **イベントハンドラー (Event Handlers)** にて、実際の副作用処理を行う。
- リポジトリを利用して永続化対象 (ドメインオブジェクト) を更新したり、ログ／履歴テーブルへの記録、外部連携などを行う。
- 例 (ドメインオブジェクトの更新):
  ```python
  class TodoCreatedHandler:
      def __init__(self, history_repo):
          self.history_repo = history_repo

      def handle(self, event: TodoCreatedEvent):
          history = TodoHistory(
              todo_id=event.todo_id,
              action='created',
              timestamp=datetime.now()
          )
          self.history_repo.save(history)
  ```
- ポイント:
  - イベントハンドラー内で **ドメインリポジトリを使っても良い** が、対象がドメインオブジェクトでない場合は別途インフラ層のサービスを利用する。
  - 複数リポジトリにまたがる処理や、集約外データへのアクセスはアプリケーションサービス側でトランザクション管理を行う。

### 4.1 ドメインオブジェクトではない対象の処理

- 履歴テーブルやログ, メール送信記録, 外部API呼び出しなど、ドメインモデルとしてのリポジトリが用意されていない場合:
  - **インフラ層のサービス (Gateway/Client/Recorder)** を使って実装する。
  - 例:
    ```python
    class AuditLogger:
        def log(self, message: str):
            # DB, ファイル, CloudWatch などへ出力
            ...
    ```

    ```python
    class TodoCreatedHandler:
        def __init__(self, logger: AuditLogger):
            self.logger = logger

        def handle(self, event: TodoCreatedEvent):
            self.logger.log(f"Todo created: {event.todo_id}")
    ```
  - 命名例: `TodoHistoryRecorder`, `NotificationSender`, `MetricsClient` など。
  - 位置づけ: ドメイン層ではなく、アプリケーション層 ／ インフラ層に配置する。

## 5. まとめ

| 処理 | 書く場所                   | 役割・注意点                                                                   |
| ---- | -------------------------- | ------------------------------------------------------------------------------ |
| 発行 | エンティティ/集約内        | 自身の状態変化をイベントとしてバッファに蓄積。副作用は呼ばない。               |
| 取得 | アプリケーションサービス層 | 発行済みのイベントを取得し、ディスパッチャに送る。トランザクション管理に注意。 |
| 処理 | イベントハンドラー         | リポジトリ or インフラサービスを呼んで永続化や外部連携などを行う。             |

本ドキュメントの内容を踏まえ、DDD設計におけるドメインイベントの同期処理フローを円滑に実装してください。