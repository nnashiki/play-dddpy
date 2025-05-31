"""Test for TodoCreateAssembler"""

import unittest
from uuid import uuid4

from dddpy.usecase.assembler import TodoCreateAssembler
from dddpy.dto.todo import TodoCreateDto


class TestTodoCreateAssembler(unittest.TestCase):
    """TodoCreateAssemblerのテストクラス"""

    def test_to_entity_minimal(self):
        """最小限のDTOからEntityを生成"""
        dto = TodoCreateDto(title="Test Todo")
        project_id_str = str(uuid4())
        
        todo = TodoCreateAssembler.to_entity(dto, project_id_str)
        
        self.assertEqual(todo.title.value, "Test Todo")
        self.assertEqual(str(todo.project_id.value), project_id_str)
        self.assertIsNone(todo.description)
        self.assertTrue(todo.dependencies.is_empty())

    def test_to_entity_with_description(self):
        """説明付きDTOからEntityを生成"""
        dto = TodoCreateDto(
            title="Test Todo",
            description="Test Description"
        )
        project_id_str = str(uuid4())
        
        todo = TodoCreateAssembler.to_entity(dto, project_id_str)
        
        self.assertEqual(todo.description.value, "Test Description")

    def test_to_entity_with_dependencies(self):
        """依存関係付きDTOからEntityを生成"""
        dep_id_str = str(uuid4())
        dto = TodoCreateDto(
            title="Test Todo",
            dependencies=[dep_id_str]
        )
        project_id_str = str(uuid4())
        
        todo = TodoCreateAssembler.to_entity(dto, project_id_str)
        
        self.assertEqual(len(todo.dependencies.values), 1)


if __name__ == '__main__':
    unittest.main()
