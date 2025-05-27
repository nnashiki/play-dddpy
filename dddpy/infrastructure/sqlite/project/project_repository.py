"""SQLite implementation of Project repository."""

from typing import Dict, List, Optional

from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.session import Session

from dddpy.domain.project.entities import Project
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.value_objects import ProjectId
from dddpy.domain.todo.entities import Todo
from dddpy.domain.todo.value_objects import TodoId
from dddpy.infrastructure.sqlite.project.project_model import ProjectModel
from dddpy.infrastructure.sqlite.todo.todo_model import TodoModel


class ProjectRepositoryImpl(ProjectRepository):
    """SQLite implementation of Project repository interface."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session."""
        self.session = session

    def find_by_id(self, project_id: ProjectId) -> Optional[Project]:
        """Find a Project by its ID."""
        try:
            project_row = self.session.query(ProjectModel).filter_by(id=project_id.value).one()
        except NoResultFound:
            return None

        project = project_row.to_entity()
        
        # Load todos for this project
        todo_rows = (
            self.session.query(TodoModel)
            .filter_by(project_id=project_id.value)
            .all()
        )
        
        # Convert todos to entities and add to project
        todos_dict: Dict[TodoId, Todo] = {}
        for todo_row in todo_rows:
            todo = todo_row.to_entity()
            todos_dict[todo.id] = todo
        
        # Load todos using the internal method
        project._load_todos(todos_dict)
        
        return project

    def find_all(self, limit: Optional[int] = None) -> List[Project]:
        """Retrieve all Project items with optional limit."""
        query = (
            self.session.query(ProjectModel)
            .order_by(desc(ProjectModel.created_at))
        )
        
        if limit is not None:
            query = query.limit(limit)
        
        project_rows = query.all()
        
        projects = []
        for project_row in project_rows:
            project = project_row.to_entity()
            
            # Load todos for this project
            todo_rows = (
                self.session.query(TodoModel)
                .filter_by(project_id=project.id.value)
                .all()
            )
            
            # Convert todos to entities and add to project
            todos_dict: Dict[TodoId, Todo] = {}
            for todo_row in todo_rows:
                todo = todo_row.to_entity()
                todos_dict[todo.id] = todo
            
            project._load_todos(todos_dict)
            projects.append(project)
        
        return projects

    def save(self, project: Project) -> None:
        """Save a Project and all its todos."""
        # Save project
        project_dto = ProjectModel.from_entity(project)
        try:
            existing_project = (
                self.session.query(ProjectModel).filter_by(id=project.id.value).one()
            )
            # Update existing project
            existing_project.name = project_dto.name
            existing_project.description = project_dto.description
            existing_project.updated_at = project_dto.updated_at
        except NoResultFound:
            # Create new project
            self.session.add(project_dto)

        # Save all todos
        for todo in project.todos:
            todo_dto = TodoModel.from_entity(todo)
            try:
                existing_todo = (
                    self.session.query(TodoModel).filter_by(id=todo.id.value).one()
                )
                # Update existing todo
                existing_todo.project_id = todo_dto.project_id
                existing_todo.title = todo_dto.title
                existing_todo.description = todo_dto.description
                existing_todo.status = todo_dto.status
                existing_todo.dependencies = todo_dto.dependencies
                existing_todo.updated_at = todo_dto.updated_at
                existing_todo.completed_at = todo_dto.completed_at
            except NoResultFound:
                # Create new todo
                self.session.add(todo_dto)

        # Remove todos that are no longer in the project
        existing_todo_ids = {todo.id.value for todo in project.todos}
        todos_to_delete = (
            self.session.query(TodoModel)
            .filter_by(project_id=project.id.value)
            .filter(~TodoModel.id.in_(existing_todo_ids))
            .all()
        )
        for todo_to_delete in todos_to_delete:
            self.session.delete(todo_to_delete)

    def delete(self, project_id: ProjectId) -> None:
        """Delete a Project and all its todos."""
        # Delete all todos in the project first
        self.session.query(TodoModel).filter_by(project_id=project_id.value).delete()
        
        # Delete the project
        self.session.query(ProjectModel).filter_by(id=project_id.value).delete()

    def find_project_by_todo_id(self, todo_id: TodoId) -> Optional[Project]:
        """Find a Project that contains the specified Todo."""
        try:
            # Find the todo first to get the project_id
            todo_row = self.session.query(TodoModel).filter_by(id=todo_id.value).one()
            project_id = ProjectId(todo_row.project_id)
            
            # Use existing find_by_id method to get the full project with todos
            return self.find_by_id(project_id)
        except NoResultFound:
            return None


def new_project_repository(session: Session) -> ProjectRepository:
    """Create a new ProjectRepository instance."""
    return ProjectRepositoryImpl(session)
