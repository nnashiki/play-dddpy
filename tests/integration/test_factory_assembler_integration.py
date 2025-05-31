"""Integration test for Factory + Assembler + Domain Events."""

import unittest
from uuid import uuid4

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import ProjectId, ProjectName, ProjectDescription
from dddpy.domain.shared.events import get_event_publisher
from dddpy.domain.todo.factories import EventAwareTodoFactory
from dddpy.domain.todo.value_objects import TodoTitle, TodoDescription
from dddpy.dto.todo import TodoCreateDto
from dddpy.usecase.assembler import TodoCreateAssembler


class TestFactoryAssemblerIntegration(unittest.TestCase):
    """統合テスト：Factory + Assembler + Domain Events"""

    def setUp(self):
        """テストの前準備"""
        # Clear any existing events
        get_event_publisher().clear_events()
        
        # Create a test project
        self.project = Project(
            id=ProjectId(uuid4()),
            name=ProjectName("Test Project"),
            description=ProjectDescription("Test Description")
        )

    def test_assembler_to_factory_to_project_flow(self):
        """Assembler → Factory → Project 統合フロー"""
        # 1. DTOからAssemblerでエンティティ作成
        dto = TodoCreateDto(
            title="Integration Test Todo",
            description="Test Description"
        )
        
        todo = TodoCreateAssembler.to_entity(dto, str(self.project.id.value))
        
        # 2. ProjectにTodoを追加
        self.project.add_todo_entity(todo)
        
        # 3. 結果確認
        self.assertEqual(len(self.project.todos), 1)
        added_todo = self.project.todos[0]
        self.assertEqual(added_todo.title.value, "Integration Test Todo")
        self.assertEqual(added_todo.project_id, self.project.id)

    def test_event_aware_factory_publishes_events(self):
        """EventAwareFactory使用時のイベント発行確認"""
        title = TodoTitle("Event Test Todo")
        description = TodoDescription("Event Test Description")
        
        # EventAwareFactoryでTodo作成
        todo = EventAwareTodoFactory.create(
            title=title,
            project_id=self.project.id,
            description=description
        )
        
        # イベントが発行されていることを確認
        events = get_event_publisher().get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "TodoCreated")
        self.assertEqual(events[0].todo_id, todo.id.value)

    def test_project_add_todo_entity_publishes_event(self):
        """Project.add_todo_entity使用時のイベント発行確認"""
        # Clear events first
        get_event_publisher().clear_events()
        
        # TodoをFactory経由で作成
        title = TodoTitle("Project Event Test")
        todo = EventAwareTodoFactory.create(
            title=title,
            project_id=self.project.id
        )
        
        # Clear TodoCreated event
        get_event_publisher().clear_events()
        
        # ProjectにTodoを追加
        self.project.add_todo_entity(todo)
        
        # TodoAddedToProjectイベントが発行されていることを確認
        events = get_event_publisher().get_events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].event_type, "TodoAddedToProject")
        self.assertEqual(events[0].project_id, self.project.id.value)
        self.assertEqual(events[0].todo_id, todo.id.value)

    def test_full_integration_with_multiple_events(self):
        """完全統合テスト：複数イベント発行"""
        get_event_publisher().clear_events()
        
        # 1. DTOからTodo作成（EventAwareFactoryベース）
        dto = TodoCreateDto(title="Full Integration Todo")
        
        # TodoCreateAssemblerを拡張してEventAwareFactoryを使用
        title_vo = TodoTitle(dto.title)
        todo = EventAwareTodoFactory.create(
            title=title_vo,
            project_id=self.project.id
        )
        
        # 2. ProjectにTodo追加
        self.project.add_todo_entity(todo)
        
        # 3. 両方のイベントが発行されていることを確認
        events = get_event_publisher().get_events()
        self.assertEqual(len(events), 2)
        
        event_types = [event.event_type for event in events]
        self.assertIn("TodoCreated", event_types)
        self.assertIn("TodoAddedToProject", event_types)


if __name__ == '__main__':
    unittest.main()
