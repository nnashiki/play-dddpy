"""Abstract Factory for Todo creation with different strategies."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from dddpy.domain.shared.clock import Clock, SystemClock
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
)

if TYPE_CHECKING:
    from dddpy.domain.project.value_objects import ProjectId


class AbstractTodoFactory(ABC):
    """Abstract factory interface for creating Todo entities with different strategies."""

    @abstractmethod
    def create_todo(
        self,
        title: TodoTitle,
        project_id: 'ProjectId',
        description: TodoDescription | None = None,
        dependencies: TodoDependencies | None = None,
        clock: Clock | None = None,
    ) -> Todo:
        """Create a Todo entity with specific creation strategy."""


class StandardTodoFactory(AbstractTodoFactory):
    """Standard Todo factory for normal todo creation."""

    def create_todo(
        self,
        title: TodoTitle,
        project_id: 'ProjectId',
        description: TodoDescription | None = None,
        dependencies: TodoDependencies | None = None,
        clock: Clock | None = None,
    ) -> Todo:
        """Create a standard Todo entity."""
        return Todo.create(
            title=title,
            project_id=project_id,
            description=description,
            dependencies=dependencies,
            clock=clock or SystemClock(),
        )


class HighPriorityTodoFactory(AbstractTodoFactory):
    """Factory for creating high-priority todos with additional validation."""

    def create_todo(
        self,
        title: TodoTitle,
        project_id: 'ProjectId',
        description: TodoDescription | None = None,
        dependencies: TodoDependencies | None = None,
        clock: Clock | None = None,
    ) -> Todo:
        """Create a high-priority Todo entity with enhanced validation."""
        # Add high-priority specific validation
        if not description:
            # High-priority todos require description
            from dddpy.domain.todo.value_objects import TodoDescription
            description = TodoDescription("High priority task - description required")
        
        # Create todo with additional metadata for high priority
        todo = Todo.create(
            title=title,
            project_id=project_id,
            description=description,
            dependencies=dependencies,
            clock=clock or SystemClock(),
        )
        
        # Future: Add priority-specific domain events or metadata
        return todo


class TodoFactoryProvider:
    """Provider class to get appropriate Todo factory based on context."""

    @staticmethod
    def get_factory(factory_type: str = "standard") -> AbstractTodoFactory:
        """Get appropriate Todo factory based on type.
        
        Args:
            factory_type: Type of factory ("standard", "high_priority")
            
        Returns:
            AbstractTodoFactory: Appropriate factory instance
            
        Raises:
            ValueError: If factory_type is not supported
        """
        # ✅ 型を統一：すべてAbstractTodoFactoryとして扱う
        factories: dict[str, AbstractTodoFactory] = {
            "standard": StandardTodoFactory(),
            "high_priority": HighPriorityTodoFactory(),
        }
        
        if factory_type not in factories:
            raise ValueError(f"Unsupported factory type: {factory_type}")
            
        return factories[factory_type]
