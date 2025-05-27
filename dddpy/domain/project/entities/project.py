"""Project entity that acts as an aggregate root containing multiple Todos."""

from datetime import datetime
from typing import Dict, List, Mapping, Optional, Set

from dddpy.domain.project.value_objects import ProjectId, ProjectName, ProjectDescription
from dddpy.domain.project.exceptions import TodoRemovalNotAllowedError
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import (
    TodoDependencies,
    TodoDescription as TodoDescriptionVO,
    TodoId,
    TodoStatus,
    TodoTitle,
)
from dddpy.domain.todo.exceptions import (
    TodoAlreadyCompletedError,
    TodoAlreadyStartedError,
    TodoCircularDependencyError,
    TodoDependencyNotCompletedError,
    TodoDependencyNotFoundError,
    TodoNotFoundError,
)


class Project:
    """Project aggregate root that manages multiple Todos and their dependencies."""

    def __init__(
        self,
        id: ProjectId,
        name: ProjectName,
        description: Optional[ProjectDescription] = None,
        todos: Optional[Dict[TodoId, Todo]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
    ):
        """Initialize a new Project aggregate."""
        self._id = id
        self._name = name
        self._description = description or ProjectDescription(None)
        self._todos = todos or {}
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

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
    def todos(self) -> List[Todo]:
        """Get all todos in the project"""
        return list(self._todos.values())
    
    @property
    def todos_mapping(self) -> Mapping[TodoId, Todo]:
        """Get todos as read-only mapping for internal operations"""
        return self._todos.copy()

    def update_name(self, new_name: ProjectName) -> None:
        """Update the Project's name"""
        self._name = new_name
        self._updated_at = datetime.now()

    def update_description(self, new_description: ProjectDescription) -> None:
        """Update the Project's description"""
        self._description = new_description
        self._updated_at = datetime.now()

    def add_todo(
        self,
        title: TodoTitle,
        description: Optional[TodoDescriptionVO] = None,
        dependencies: Optional[List[TodoId]] = None,
    ) -> Todo:
        """Add a new Todo to the project with dependency validation"""
        # Validate dependencies exist within this project
        if dependencies:
            self._validate_dependencies_exist(dependencies)
            deps = TodoDependencies.from_list(dependencies)
        else:
            deps = None

        # Create todo with project_id
        todo = Todo.create(title, self._id, description, deps)
        
        # Validate no circular dependencies
        if dependencies:
            self._validate_no_circular_dependency(todo.id, dependencies)

        self._todos[todo.id] = todo
        self._updated_at = datetime.now()
        return todo

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
        self._updated_at = datetime.now()

    def get_todo(self, todo_id: TodoId) -> Todo:
        """Get a Todo by its ID"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()
        return self._todos[todo_id]

    def update_todo_by_id(
        self, 
        todo_id: TodoId, 
        title: Optional[TodoTitle] = None,
        description: Optional[TodoDescriptionVO] = None,
        dependencies: Optional[List[TodoId]] = None
    ) -> Todo:
        """Update a Todo by ID"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()
        
        todo = self._todos[todo_id]
        
        if title is not None:
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
        
        self._updated_at = datetime.now()
        return todo

    def start_todo_by_id(self, todo_id: TodoId) -> Todo:
        """Start a Todo by ID after validating all dependencies are completed"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()
        
        todo = self._todos[todo_id]
        
        # Check if all dependencies are completed
        if not self._can_start_todo(todo):
            raise TodoDependencyNotCompletedError('Cannot start todo because dependencies are not completed')
        
        todo.start()
        self._updated_at = datetime.now()
        return todo

    def complete_todo_by_id(self, todo_id: TodoId) -> Todo:
        """Complete a Todo by ID"""
        if todo_id not in self._todos:
            raise TodoNotFoundError()
        
        todo = self._todos[todo_id]
        todo.complete()
        self._updated_at = datetime.now()
        return todo

    def _validate_dependencies_exist(self, dependency_ids: List[TodoId]) -> None:
        """Validate that all dependency todos exist within this project"""
        for dep_id in dependency_ids:
            if dep_id not in self._todos:
                raise TodoDependencyNotFoundError(str(dep_id.value))

    def _validate_no_circular_dependency(self, todo_id: TodoId, new_dependencies: List[TodoId]) -> None:
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
            deps_to_check = new_dependencies if current_id == todo_id else current_todo.dependencies.values
            
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

    @staticmethod
    def create(name: str, description: Optional[str] = None) -> 'Project':
        """Create a new Project"""
        project_name = ProjectName(name)
        project_description = ProjectDescription(description)
        
        return Project(ProjectId.generate(), project_name, project_description)
    
    @staticmethod
    def from_persistence(
        id: ProjectId,
        name: str,
        description: Optional[str],
        todos: Dict[TodoId, Todo],
        created_at: datetime,
        updated_at: datetime,
    ) -> 'Project':
        """Create a Project from persistence data (for infrastructure layer)"""
        project_name = ProjectName(name)
        project_description = ProjectDescription(description)
        
        return Project(
            id=id,
            name=project_name,
            description=project_description,
            todos=todos,
            created_at=created_at,
            updated_at=updated_at,
        )
    
    def _load_todos(self, todos: Dict[TodoId, Todo]) -> None:
        """Load todos for internal use (for infrastructure layer)"""
        self._todos = todos
