"""SQLite implementation of Project repository."""


from sqlalchemy import desc
from sqlalchemy.exc import NoResultFound
from sqlalchemy.orm.session import Session

from dddpy.domain.project.entities import Project
from dddpy.domain.project.repositories import ProjectRepository
from dddpy.domain.project.value_objects import ProjectId
from dddpy.infrastructure.sqlite.project.project_mapper import ProjectMapper
from dddpy.infrastructure.sqlite.project.project_model import ProjectModel
from dddpy.infrastructure.sqlite.todo.todo_model import TodoModel
from dddpy.infrastructure.sqlite.todo.todo_mapper import TodoMapper


class ProjectRepositoryImpl(ProjectRepository):
    """SQLite implementation of Project repository interface."""

    def __init__(self, session: Session):
        """Initialize repository with SQLAlchemy session."""
        self.session = session

    def find_by_id(self, project_id: ProjectId) -> Project | None:
        """Find a Project by its ID."""
        try:
            project_row = (
                self.session.query(ProjectModel).filter_by(id=project_id.value).one()
            )
        except NoResultFound:
            return None

        # Mapper で Project + Todos を組み立て
        todo_rows = (
            self.session.query(TodoModel).filter_by(project_id=project_id.value).all()
        )
        return ProjectMapper.to_entity(project_row, todo_rows)

    def find_all(self, limit: int | None = None) -> list[Project]:
        """Retrieve all Project items with optional limit."""
        query = self.session.query(ProjectModel).order_by(desc(ProjectModel.created_at))

        if limit is not None:
            query = query.limit(limit)

        project_rows = query.all()

        projects = []
        for project_row in project_rows:
            todo_rows = (
                self.session.query(TodoModel).filter_by(project_id=project_row.id).all()
            )
            projects.append(ProjectMapper.to_entity(project_row, todo_rows))

        return projects

    def save(self, project: Project) -> None:
        """Save a Project and all its todos."""
        # Save project
        project_dto = ProjectMapper.from_entity(project)
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

        # Save all todos using TodoMapper
        for todo in project.todos:
            todo_dto = TodoMapper.from_entity(todo)
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
        if existing_todo_ids:
            todos_to_delete = (
                self.session.query(TodoModel)
                .filter_by(project_id=project.id.value)
                .filter(~TodoModel.id.in_(existing_todo_ids))
                .all()
            )
        else:
            # If no todos exist in project, delete all todos for this project
            todos_to_delete = (
                self.session.query(TodoModel)
                .filter_by(project_id=project.id.value)
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


def new_project_repository(session: Session) -> ProjectRepository:
    """Create a new ProjectRepository instance."""
    return ProjectRepositoryImpl(session)
