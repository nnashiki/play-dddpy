"""Factory strategy selector for different Todo creation scenarios."""

from enum import Enum
from typing import TYPE_CHECKING

from dddpy.domain.shared.clock import Clock
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.factories import TodoFactory
from dddpy.domain.todo.factories.event_aware_todo_factory import EventAwareTodoFactory
from dddpy.domain.todo.factories.abstract_todo_factory import (
    StandardTodoFactory,
    HighPriorityTodoFactory,
)
from dddpy.domain.todo.value_objects import (
    TodoTitle,
    TodoDescription,
    TodoDependencies,
)

if TYPE_CHECKING:
    from dddpy.domain.project.value_objects import ProjectId


class TodoCreationStrategy(Enum):
    """Todo creation strategy enumeration."""
    
    STANDARD = "standard"
    HIGH_PRIORITY = "high_priority"
    EVENT_AWARE = "event_aware"
    LEGACY = "legacy"


class TodoFactorySelector:
    """Factory selector to choose appropriate Todo creation strategy."""

    @staticmethod
    def create_todo(
        strategy: TodoCreationStrategy,
        title: TodoTitle,
        project_id: 'ProjectId',
        description: TodoDescription | None = None,
        dependencies: TodoDependencies | None = None,
        clock: Clock | None = None,
    ) -> Todo:
        """Create Todo using specified strategy.
        
        Args:
            strategy: Creation strategy to use
            title: Todo title
            project_id: Project ID
            description: Optional description
            dependencies: Optional dependencies
            clock: Optional clock
            
        Returns:
            Todo: Created Todo entity
            
        Raises:
            ValueError: If strategy is not supported
        """
        if strategy == TodoCreationStrategy.STANDARD:
            factory = StandardTodoFactory()
            return factory.create_todo(title, project_id, description, dependencies, clock)
            
        elif strategy == TodoCreationStrategy.HIGH_PRIORITY:
            factory = HighPriorityTodoFactory()
            return factory.create_todo(title, project_id, description, dependencies, clock)
            
        elif strategy == TodoCreationStrategy.EVENT_AWARE:
            return EventAwareTodoFactory.create(title, project_id, description, dependencies, clock)
            
        elif strategy == TodoCreationStrategy.LEGACY:
            # Use legacy TodoFactory.create for backward compatibility
            return TodoFactory.create(title, project_id, description, dependencies, clock)
            
        else:
            raise ValueError(f"Unsupported creation strategy: {strategy}")

    @staticmethod
    def get_recommended_strategy(
        has_dependencies: bool = False,
        is_high_priority: bool = False,
        needs_events: bool = False,
    ) -> TodoCreationStrategy:
        """Get recommended strategy based on context.
        
        Args:
            has_dependencies: Whether todo has dependencies
            is_high_priority: Whether todo is high priority
            needs_events: Whether domain events are needed
            
        Returns:
            TodoCreationStrategy: Recommended strategy
        """
        # Event-aware strategy if events are needed
        if needs_events:
            return TodoCreationStrategy.EVENT_AWARE
            
        # High priority strategy for important todos
        if is_high_priority:
            return TodoCreationStrategy.HIGH_PRIORITY
            
        # Standard strategy for most cases
        return TodoCreationStrategy.STANDARD
