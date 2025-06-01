"""Integration test for Factory + Assembler + Domain Events (Updated)."""

import unittest
from uuid import uuid4

from dddpy.domain.project.entities import Project
from dddpy.domain.project.value_objects import ProjectId, ProjectName, ProjectDescription
from dddpy.domain.shared.events import get_event_publisher
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import TodoTitle, TodoDescription
from dddpy.dto.todo import TodoCreateDto
from dddpy.dto.project import AddTodoToProjectDto
from dddpy.usecase.assembler import TodoCreateAssembler


class TestFactoryAssemblerIntegrationUpdated(unittest.TestCase):
    """統合テスト：Factory + Assembler + Domain Events (修正版)"""

    def setUp(self):
        """テストの前準備"""
        # Create a test project directly (without using Project.create() to avoid ProjectCreated event)
        self.project = Project(
            id=ProjectId(uuid4()),
            name=ProjectName("Test Project"),
            description=ProjectDescription("Test Description"),
            event_publisher=get_event_publisher()
        )
        
        # Clear any existing events after project creation
        get_event_publisher().clear_events()

    def test_assembler_with_todo_create_dto(self):
        """TodoCreateDto使用の統合フロー"""
        # 1. TodoCreateDtoからAssemblerでエンティティ作成
        dto = TodoCreateDto(
            title="TodoCreateDto Test",
            description="Test Description"
        )
        
        todo = TodoCreateAssembler.to_entity(dto, str(self.project.id.value))
        
        # 2. ProjectにTodoを追加
        self.project.add_todo_entity(todo)
        
        # 3. 結果確認
        self.assertEqual(len(self.project.todos), 1)
        added_todo = self.project.todos[0]
        self.assertEqual(added_todo.title.value, "TodoCreateDto Test")

    def test_assembler_with_add_todo_dto(self):
        """AddTodoToProjectDto使用の統合フロー（実際のUseCaseと同じ）"""
        # 1. AddTodoToProjectDtoからAssemblerでエンティティ作成
        dto = AddTodoToProjectDto(
            title="AddTodoToProject Test",
            description="Test Description"
        )
        
        # ✅ 修正版：DTOを直接渡す（型変換不要）
        todo = TodoCreateAssembler.to_entity(dto, str(self.project.id.value))
        
        # 2. ProjectにTodoを追加
        self.project.add_todo_entity(todo)
        
        # 3. 結果確認
        self.assertEqual(len(self.project.todos), 1)
        added_todo = self.project.todos[0]
        self.assertEqual(added_todo.title.value, "AddTodoToProject Test")

    def test_event_aware_assembler_with_add_todo_dto(self):
        """Todo.create + AddTodoToProjectDto統合テスト"""
        get_event_publisher().clear_events()
        
        # AddTodoToProjectDtoを直接使用
        dto = AddTodoToProjectDto(
            title="Event Aware Test",
            description="Test Description"
        )
        
        # Todoを直接作成
        todo = Todo.create(
            title=TodoTitle(dto.title),
            project_id=self.project.id,
            description=TodoDescription(dto.description) if dto.description else None,
            event_publisher=get_event_publisher(),
        )
        
        # ProjectにTodo追加
        self.project.add_todo_entity(todo)
        
        # 両方のイベントが発行されていることを確認
        events = get_event_publisher().get_events()
        self.assertEqual(len(events), 2)
        
        event_types = [event.event_type for event in events]
        self.assertIn("TodoCreated", event_types)
        self.assertIn("TodoAddedToProject", event_types)

    def test_protocol_compatibility(self):
        """Protocol互換性テスト - 同じAssemblerで異なるDTOを処理"""
        get_event_publisher().clear_events()
        
        # TodoCreateDto
        todo_dto = TodoCreateDto(title="Protocol Test 1")
        todo1 = TodoCreateAssembler.to_entity(todo_dto, str(self.project.id.value))
        
        # AddTodoToProjectDto
        add_dto = AddTodoToProjectDto(title="Protocol Test 2")
        todo2 = TodoCreateAssembler.to_entity(add_dto, str(self.project.id.value))
        
        # 両方とも正常に作成できることを確認
        self.assertEqual(todo1.title.value, "Protocol Test 1")
        self.assertEqual(todo2.title.value, "Protocol Test 2")
        self.assertEqual(todo1.project_id, self.project.id)
        self.assertEqual(todo2.project_id, self.project.id)


if __name__ == '__main__':
    unittest.main()
