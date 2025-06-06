"""Project entity that acts as an aggregate root containing multiple Todos."""

from collections.abc import Mapping
from datetime import datetime
from typing import TYPE_CHECKING

from dddpy.domain.project.exceptions import (
    DuplicateTodoTitleError,
    TodoRemovalNotAllowedError,
    TooManyTodosError,
)
from dddpy.domain.project.value_objects import (
    ProjectDescription,
    ProjectId,
    ProjectName,
)
from dddpy.domain.shared.clock import Clock, SystemClock
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.exceptions import (
    TodoCircularDependencyError,
    TodoDependencyNotCompletedError,
    TodoDependencyNotFoundError,
    TodoNotFoundError,
)
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoId,
    TodoTitle,
)
from dddpy.domain.todo.value_objects import (
    TodoDescription as TodoDescriptionVO,
)
from dddpy.domain.todo.events import TodoAddedToProjectEvent
from dddpy.domain.project.events.project_created_event import ProjectCreatedEvent

if TYPE_CHECKING:
    from dddpy.domain.shared.events import DomainEventPublisher, DomainEvent


class Project:
    """Project aggregate root that manages multiple Todos and their dependencies."""

    # Domain constraints
    MAX_TODO_COUNT = 1000

    def __init__(
        self,
        id: ProjectId,
        name: ProjectName,
        description: ProjectDescription | None = None,
        todos: dict[TodoId, Todo] | None = None,
        clock: Clock | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        event_publisher: 'DomainEventPublisher | None' = None,
    ):
        """Initialize a new Project aggregate."""
        self._id = id
        self._name = name
        self._description = description or ProjectDescription(None)
        self._todos = todos or {}
        self._clock = clock or SystemClock()
        self._created_at = created_at or self._clock.now()
        self._updated_at = updated_at or self._clock.now()
        self._event_publisher = event_publisher
        self._events: list['DomainEvent'] = []

    def __eq__(self, obj: object) -> bool:
        if isinstance(obj, Project):
            return self.id == obj.id
        return False

    @property
    def id(self) -> ProjectId:
        """Get the Project's unique identifier"""
        return self._id

    @property
    def name(self) -> ProjectName:
        """Get the Project's name"""
        return self._name

    @property
    def description(self) -> ProjectDescription:
        """Get the Project's description"""
        return self._description

    @property
    def created_at(self) -> datetime:
        """Get the Project's creation timestamp"""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Get the Project's last update timestamp"""
        return self._updated_at

    @property
    def todos(self) -> list[Todo]:
        """Get all todos in the project"""
        return list(self._todos.values())

    @property
    def todos_mapping(self) -> Mapping[TodoId, Todo]:
        """Get todos as read-only mapping for internal operations"""
        return self._todos.copy()

    def get_events(self) -> list['DomainEvent']:
        """Get all events that have been published."""
        return self._events.copy()

    def has_events(self) -> bool:
        """Check if there are any events."""
        return len(self._events) > 0

    def clear_events(self) -> None:
        """Clear all events."""
        self._events.clear()

    def _publish_event(self, event: 'DomainEvent') -> None:
        """Publish a domain event."""
        if self._event_publisher:
            self._event_publisher.publish(event)
        self._events.append(event)

    def update_name(self, new_name: ProjectName) -> None:
        """Update the Project's name"""
        self._name = new_name
        self._updated_at = self._clock.now()

    def update_description(self, new_description: ProjectDescription) -> None:
        """Update the Project's description"""
        self._description = new_description
        self._updated_at = self._clock.now()

    def add_todo(
        self,
        title: TodoTitle,
        description: TodoDescriptionVO | None = None,
        dependencies: list[TodoId] | None = None,
    ) -> Todo:
        """Add a new Todo to the project with dependency validation"""
        # Validate todo count limit
        self._validate_todo_limit()

        # Validate no duplicate title
        self._validate_no_duplicate_title(title)

        # Validate dependencies exist within this project
        if dependencies:
            self._validate_dependencies_exist(dependencies)
            deps = TodoDependencies.from_list(dependencies)
        else:
            deps = None

        # Create todo with project_id
        todo = Todo.create(
            title,
            self._id,
            description,
            deps,
            self._clock,
            event_publisher=self._event_publisher,
        )

        # Validate no circular dependencies
        if dependencies:
            self._validate_no_circular_dependency(todo.id, dependencies)

        self._todos[todo.id] = todo
        self._updated_at = self._clock.now()
        return todo

    def add_todo_entity(self, todo: Todo) -> None:
        """Add an existing Todo entity to the project with validation"""
        # Validate that the todo belongs to this project
        if todo.project_id != self._id:
            raise ValueError(
                f'Todo project_id {todo.project_id} does not match this project {self._id}'
            )

        # Validate todo count limit
        self._validate_todo_limit()

        # Validate no duplicate title
        self._validate_no_duplicate_title(todo.title)

        # Validate dependencies exist within this project
        if not todo.dependencies.is_empty():
            self._validate_dependencies_exist(list(todo.dependencies.values))

            # Validate no circular dependencies
            self._validate_no_circular_dependency(
                todo.id, list(todo.dependencies.values)
            )

        # Add todo to project
        self._todos[todo.id] = todo
        self._updated_at = self._clock.now()

        # Publish domain event
        event = TodoAddedToProjectEvent(
            project_id=self._id.value,
            todo_id=todo.id.value,
            todo_title=todo.title.value,
            occurred_at=self._updated_at,
        )
        self._publish_event(event)

    def remove_todo(self, todo_id: TodoId) -> None:
        """Remove a Todo from the project"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()

        # Check if any other todos depend on this one
        dependent_todos = []
        for other_todo in self._todos.values():
            if other_todo.dependencies.contains(todo_id):
                dependent_todos.append(str(other_todo.id.value))

        if dependent_todos:
            raise TodoRemovalNotAllowedError(str(todo_id.value), dependent_todos)

        del self._todos[todo_id]
        self._updated_at = self._clock.now()

    def get_todo(self, todo_id: TodoId) -> Todo:
        """Get a Todo by its ID"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()
        return self._todos[todo_id]

    def update_todo_by_id(
        self,
        todo_id: TodoId,
        title: TodoTitle | None = None,
        description: TodoDescriptionVO | None = None,
        dependencies: list[TodoId] | None = None,
    ) -> Todo:
        """Update a Todo by ID"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()

        todo = self._todos[todo_id]

        if title is not None:
            # Validate no duplicate title (excluding current todo)
            self._validate_no_duplicate_title_excluding(title, todo_id)
            todo.update_title(title)

        if description is not None:
            todo.update_description(description)

        if dependencies is not None:
            # Validate dependencies exist
            self._validate_dependencies_exist(dependencies)

            # Validate no circular dependencies
            self._validate_no_circular_dependency(todo_id, dependencies)

            # Update dependencies
            deps = TodoDependencies.from_list(dependencies, self_id=todo_id)
            todo._set_dependencies(deps)

        self._updated_at = self._clock.now()
        return todo

    def start_todo_by_id(self, todo_id: TodoId) -> Todo:
        """Start a Todo by ID after validating all dependencies are completed"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()

        todo = self._todos[todo_id]

        # Check if all dependencies are completed
        if not self._can_start_todo(todo):
            raise TodoDependencyNotCompletedError(
                'Cannot start todo because dependencies are not completed'
            )

        todo.start()
        self._updated_at = self._clock.now()
        return todo

    def complete_todo_by_id(self, todo_id: TodoId) -> Todo:
        """Complete a Todo by ID"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()

        todo = self._todos[todo_id]
        todo.complete()
        self._updated_at = self._clock.now()
        return todo

    def _validate_dependencies_exist(self, dependency_ids: list[TodoId]) -> None:
        """Validate that all dependency todos exist within this project"""
        for dep_id in dependency_ids:
            if dep_id not in self._todos:
                raise TodoDependencyNotFoundError(str(dep_id.value))

    def _validate_no_circular_dependency(
        self, todo_id: TodoId, new_dependencies: list[TodoId]
    ) -> None:
        """Validate that setting new dependencies would not create circular dependencies"""
        visited = set()

        def dfs(current_id: TodoId) -> bool:
            if current_id == todo_id:
                return True
            if current_id in visited:
                return False
            visited.add(current_id)

            current_todo = self._todos.get(current_id)
            if not current_todo:
                return False

            # Use new dependencies if checking the original todo, otherwise use existing dependencies
            deps_to_check = (
                new_dependencies
                if current_id == todo_id
                else current_todo.dependencies.values
            )

            for dep_id in deps_to_check:
                if dfs(dep_id):
                    return True
            return False

        for dep_id in new_dependencies:
            if dfs(dep_id):
                raise TodoCircularDependencyError(
                    f'Setting dependency {dep_id.value} would create a circular dependency'
                )

    def _can_start_todo(self, todo: Todo) -> bool:
        """Check if a todo can be started (all dependencies are completed)"""
        if todo.dependencies.is_empty():
            return True

        for dep_id in todo.dependencies.values:
            dep_todo = self._todos.get(dep_id)
            if not dep_todo or not dep_todo.is_completed:
                return False
        return True

    def _validate_todo_limit(self) -> None:
        """Validate that adding a new todo would not exceed the limit"""
        if len(self._todos) >= self.MAX_TODO_COUNT:
            raise TooManyTodosError(len(self._todos), self.MAX_TODO_COUNT)

    def _validate_no_duplicate_title(self, title: TodoTitle) -> None:
        """Validate that the title is not already used by another todo"""
        for todo in self._todos.values():
            if todo.title.value == title.value:
                raise DuplicateTodoTitleError(title.value)

    def _validate_no_duplicate_title_excluding(
        self, title: TodoTitle, exclude_todo_id: TodoId
    ) -> None:
        """Validate that the title is not already used by another todo (excluding a specific todo)"""
        for todo_id, todo in self._todos.items():
            if todo_id != exclude_todo_id and todo.title.value == title.value:
                raise DuplicateTodoTitleError(title.value)

    def _publish_todo_added_event(self, todo: Todo) -> None:
        """Publish TodoAddedToProjectEvent when a todo is added to the project."""
        event = TodoAddedToProjectEvent(
            project_id=self._id.value,
            todo_id=todo.id.value,
            todo_title=todo.title.value,
            occurred_at=self._updated_at,
        )
        self._publish_event(event)

    @staticmethod
    def create(
        name: str,
        description: str | None = None,
        event_publisher: 'DomainEventPublisher | None' = None,
    ) -> 'Project':
        """Create a new Project"""
        project_name = ProjectName(name)
        project_description = ProjectDescription(description)
        project_id = ProjectId.generate()

        project = Project(
            project_id,
            project_name,
            project_description,
            event_publisher=event_publisher,
        )

        # Publish ProjectCreated event
        event = ProjectCreatedEvent(
            project_id=project.id.value,
            name=name,
            description=description,
            occurred_at=project.created_at,
        )
        project._publish_event(event)

        return project
