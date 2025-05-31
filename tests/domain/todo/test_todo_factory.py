"""Test for TodoFactory"""

import unittest
from uuid import uuid4

from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.shared.clock import FixedClock
from dddpy.domain.todo.factories import TodoFactory
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
    TodoId,
)
from datetime import datetime


class TestTodoFactory(unittest.TestCase):
    """TodoFactoryのテストクラス"""

    def setUp(self):
        """テストの前準備"""
        self.fixed_time = datetime(2023, 1, 1, 12, 0, 0)
        self.clock = FixedClock(self.fixed_time)
        self.project_id = ProjectId(uuid4())

    def test_create_todo_with_minimal_params(self):
        """最小限のパラメータでTodoを作成"""
        title = TodoTitle("Test Todo")
        
        todo = TodoFactory.create(
            title=title,
            project_id=self.project_id,
            clock=self.clock
        )
        
        self.assertEqual(todo.title.value, "Test Todo")
        self.assertEqual(todo.project_id, self.project_id)
        self.assertIsNone(todo.description)
        self.assertTrue(todo.dependencies.is_empty())
        self.assertEqual(todo.created_at, self.fixed_time)

    def test_create_todo_with_description(self):
        """説明付きでTodoを作成"""
        title = TodoTitle("Test Todo")
        description = TodoDescription("Test Description")
        
        todo = TodoFactory.create(
            title=title,
            project_id=self.project_id,
            description=description,
            clock=self.clock
        )
        
        self.assertEqual(todo.description.value, "Test Description")

    def test_create_todo_with_dependencies(self):
        """依存関係付きでTodoを作成"""
        title = TodoTitle("Test Todo")
        dep_id = TodoId(uuid4())
        dependencies = TodoDependencies.from_list([dep_id])
        
        todo = TodoFactory.create(
            title=title,
            project_id=self.project_id,
            dependencies=dependencies,
            clock=self.clock
        )
        
        self.assertTrue(todo.dependencies.contains(dep_id))


if __name__ == '__main__':
    unittest.main()
