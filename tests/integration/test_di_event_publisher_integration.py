"""DI統一化の動作確認テスト

ProjectFactory と TodoFactory で明示的にevent_publisherを渡すことができるかテストする
統合テストとして、複数のレイヤーにまたがるDI統一化の動作を検証する。
"""

from uuid import uuid4
from dddpy.domain.project.factories.project_factory import ProjectFactory
from dddpy.domain.project.value_objects import ProjectName, ProjectDescription
from dddpy.domain.todo.factories.todo_factory import TodoFactory
from dddpy.domain.todo.factories.abstract_todo_factory import (
    StandardTodoFactory,
    HighPriorityTodoFactory,
)
from dddpy.domain.todo.factories.todo_factory_selector import (
    TodoFactorySelector,
    TodoCreationStrategy,
)
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription as TodoDescriptionVO,
)
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.shared.events import DomainEventPublisher


class MockEventPublisher(DomainEventPublisher):
    """モックイベントパブリッシャー"""

    def __init__(self):
        self.published_events = []

    def publish(self, event):
        self.published_events.append(event)
        print(f'📢 Event published: {type(event).__name__}')

    def set_session(self, session):
        pass


def test_project_factory_with_event_publisher():
    """ProjectFactoryでevent_publisherを明示的に渡すテスト"""
    print('🧪 Test: ProjectFactory with explicit event_publisher')

    mock_publisher = MockEventPublisher()

    # ProjectFactoryを使って明示的にevent_publisherを渡す
    project = ProjectFactory.create(
        name=ProjectName('Test Project'),
        description=ProjectDescription('Test Description'),
        event_publisher=mock_publisher,
    )

    print(f'✅ Project created: {project.name.value}')
    print(f'📊 Events published: {len(mock_publisher.published_events)}')

    # ProjectCreatedEventが発行されているはず
    assert len(mock_publisher.published_events) > 0
    print('✅ Project creation event published successfully')


def test_todo_factory_with_event_publisher():
    """TodoFactoryでevent_publisherを明示的に渡すテスト"""
    print('\n🧪 Test: TodoFactory with explicit event_publisher')

    mock_publisher = MockEventPublisher()
    project_id = ProjectId.generate()

    # TodoFactoryを使って明示的にevent_publisherを渡す
    todo = TodoFactory.create(
        title=TodoTitle('Test Todo'),
        project_id=project_id,
        description=TodoDescriptionVO('Test Todo Description'),
        event_publisher=mock_publisher,
    )

    print(f'✅ Todo created: {todo.title.value}')
    print(f'📊 Events published: {len(mock_publisher.published_events)}')
    print('✅ Todo creation with event publisher successful')


def test_abstract_todo_factory_with_event_publisher():
    """AbstractTodoFactoryでevent_publisherを明示的に渡すテスト"""
    print('\n🧪 Test: AbstractTodoFactory with explicit event_publisher')

    mock_publisher = MockEventPublisher()
    project_id = ProjectId.generate()

    # StandardTodoFactoryでevent_publisherを渡す
    standard_factory = StandardTodoFactory()
    todo1 = standard_factory.create_todo(
        title=TodoTitle('Standard Todo'),
        project_id=project_id,
        description=TodoDescriptionVO('Standard description'),
        event_publisher=mock_publisher,
    )

    # HighPriorityTodoFactoryでevent_publisherを渡す
    high_priority_factory = HighPriorityTodoFactory()
    todo2 = high_priority_factory.create_todo(
        title=TodoTitle('High Priority Todo'),
        project_id=project_id,
        event_publisher=mock_publisher,
    )

    print(f'✅ Standard Todo created: {todo1.title.value}')
    print(f'✅ High Priority Todo created: {todo2.title.value}')
    print(f'📊 Events published: {len(mock_publisher.published_events)}')
    print('✅ Abstract factory with event publisher successful')


def test_todo_factory_selector_with_event_publisher():
    """TodoFactorySelectorで全戦略でevent_publisherを渡すテスト"""
    print('\n🧪 Test: TodoFactorySelector with explicit event_publisher')

    mock_publisher = MockEventPublisher()
    project_id = ProjectId.generate()

    strategies = [
        TodoCreationStrategy.STANDARD,
        TodoCreationStrategy.HIGH_PRIORITY,
        TodoCreationStrategy.ENTITY_DIRECT,
        TodoCreationStrategy.LEGACY,
    ]

    for i, strategy in enumerate(strategies):
        todo = TodoFactorySelector.create_todo(
            strategy=strategy,
            title=TodoTitle(f'Todo {strategy.value} {i}'),
            project_id=project_id,
            description=TodoDescriptionVO(f'Description for {strategy.value}'),
            event_publisher=mock_publisher,
        )
        print(f'✅ {strategy.value} Todo created: {todo.title.value}')

    print(f'📊 Events published: {len(mock_publisher.published_events)}')
    print('✅ All TodoFactorySelector strategies with event publisher successful')


def test_integration_scenario():
    """統合シナリオ: ProjectにTodoを追加する完全なフロー"""
    print('\n🧪 Integration Test: Complete Project + Todo creation flow')

    mock_publisher = MockEventPublisher()

    # 1. ProjectFactoryでプロジェクト作成
    project = ProjectFactory.create(
        name=ProjectName('Integration Test Project'),
        description=ProjectDescription('Complete integration test'),
        event_publisher=mock_publisher,
    )

    # 2. プロジェクトにevent_publisherを設定
    project.set_event_publisher(mock_publisher)

    # 3. TodoFactoryでTodo作成してプロジェクトに追加
    todo1 = TodoFactory.create(
        title=TodoTitle('Integration Todo 1'),
        project_id=project.id,
        description=TodoDescriptionVO('First todo for integration test'),
        event_publisher=mock_publisher,
    )

    todo2 = TodoFactory.create(
        title=TodoTitle('Integration Todo 2'),
        project_id=project.id,
        description=TodoDescriptionVO('Second todo for integration test'),
        event_publisher=mock_publisher,
    )

    # 4. プロジェクトにTodoを追加（ドメインエンティティレベル）
    project.add_todo_entity(todo1)
    project.add_todo_entity(todo2)

    print(f"✅ Project '{project.name.value}' created with {len(project.todos)} todos")
    print(f'📊 Total events published: {len(mock_publisher.published_events)}')

    # 5. イベントの内容を確認
    for i, event in enumerate(mock_publisher.published_events):
        print(f'  Event {i + 1}: {type(event).__name__}')

    print('✅ Complete integration test successful')


def test_all_di_integration():
    """すべてのDI統一化テストを実行する統合テスト"""
    print('🚀 DI統一化の動作確認テスト開始')
    print('=' * 60)

    try:
        test_project_factory_with_event_publisher()
        test_todo_factory_with_event_publisher()
        test_abstract_todo_factory_with_event_publisher()
        test_todo_factory_selector_with_event_publisher()
        test_integration_scenario()

        print('\n' + '=' * 60)
        print('🎉 すべてのDI統一化テストが正常に完了しました！')
        print('\n✅ 達成された改善点:')
        print('  - ProjectFactoryでevent_publisherの明示的注入')
        print('  - TodoFactoryでevent_publisherの明示的注入')
        print('  - AbstractTodoFactoryでevent_publisherの統一')
        print('  - TodoFactorySelectorで全戦略の統一')
        print('  - 暗黙的なグローバル依存の排除')
        print('  - テスト時のMockPublisher注入が可能')

    except Exception as e:
        print(f'\n❌ テストエラー: {e}')
        raise


if __name__ == '__main__':
    # 直接実行時はすべてのテストを実行
    test_all_di_integration()
