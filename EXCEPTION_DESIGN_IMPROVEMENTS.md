# 例外設計の改善について

このプロジェクトでは、ドメイン例外からHTTPエラーへの一元的なマッピングを実装し、プレゼンテーション層での例外処理の保守性を向上させました。

## 実装内容

### 1. 中央集約された例外ハンドラー

**ファイル**: `dddpy/presentation/api/error_handlers.py`

- すべてのドメイン例外をHTTPステータスコードにマッピング
- 統一的なエラーレスポンス形式の提供
- 汎用例外（ValueError、Exception）の処理

### 2. 統一的なエラーレスポンス

**ファイル**: `dddpy/presentation/api/error_schemas.py`

- Pydanticベースのエラーレスポンススキーマ
- 構造化されたエラー情報の提供
- API仕様書への自動統合

### 3. エンドポイントの簡素化

**修正対象**:
- `dddpy/presentation/api/project/handlers/project_api_route_handler.py`
- `dddpy/presentation/api/todo/handlers/todo_api_route_handler.py`

各エンドポイントから重複するtry-except処理を削除し、ビジネスロジックに集中できるよう改善しました。

## 処理される例外

### プロジェクト関連
- `ProjectNotFoundError` → HTTP 404
- `ProjectDeletionNotAllowedError` → HTTP 400
- `TodoRemovalNotAllowedError` → HTTP 400
- `DuplicateTodoTitleError` → HTTP 400
- `TooManyTodosError` → HTTP 400

### Todo関連
- `TodoNotFoundError` → HTTP 404
- `TodoAlreadyStartedError` → HTTP 400
- `TodoAlreadyCompletedError` → HTTP 400
- `TodoNotStartedError` → HTTP 400
- `TodoDependencyNotFoundError` → HTTP 400
- `TodoDependencyNotCompletedError` → HTTP 400
- `TodoCircularDependencyError` → HTTP 400
- `SelfDependencyError` → HTTP 400
- `TooManyDependenciesError` → HTTP 400

### 汎用例外
- `ValueError` → HTTP 400
- `Exception` → HTTP 500（Generic Error）

## エラーレスポンス形式

```json
{
  "detail": "Project not found",
  "error_type": "ProjectNotFoundError"
}
```

## 利点

1. **保守性の向上**: 例外処理が中央に集約され、修正・追加が容易
2. **重複コードの削減**: エンドポイントでのtry-except文が不要
3. **一貫性**: 全APIで統一されたエラーレスポンス形式
4. **拡張性**: 新しい例外の追加が簡単
5. **テストの簡素化**: エンドポイントのテストでは業務ロジックに集中可能

## 今後の推奨事項

1. **具体的なドメイン例外の使用**: ValueErrorなどの汎用例外をより具体的なドメイン例外に置き換える
2. **エラーコードの追加**: より詳細なエラー分類のためのエラーコード体系の導入
3. **国際化対応**: 多言語でのエラーメッセージ対応
4. **ログ連携**: 例外発生時の詳細なログ出力機能の追加
