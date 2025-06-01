"""Main application entry point for the API."""

import logging
from contextlib import asynccontextmanager
from logging import config

from fastapi import FastAPI

from dddpy.infrastructure.sqlite.database import create_tables, engine
from dddpy.presentation.api.project.handlers.project_api_route_handler import (
    ProjectApiRouteHandler,
)
from dddpy.presentation.api.project.handlers.project_todo_api_route_handler import (
    ProjectTodoApiRouteHandler,
)
from dddpy.presentation.api.error_handlers import add_exception_handlers

config.fileConfig('logging.conf', disable_existing_loggers=False)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables on startup and cleanup on shutdown."""
    create_tables()
    yield
    engine.dispose()


app = FastAPI(
    title='DDD Todo API',
    description='A RESTful API for managing todos using Domain-Driven Design principles.',
    version='2.0.0',
    lifespan=lifespan,
)

project_route_handler = ProjectApiRouteHandler()
project_route_handler.register_routes(app)

project_todo_route_handler = ProjectTodoApiRouteHandler()
project_todo_route_handler.register_routes(app)

# Register central exception handlers
add_exception_handlers(app)
