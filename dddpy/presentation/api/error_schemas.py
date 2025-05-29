"""Standardized error response schemas for the API."""

from pydantic import BaseModel, Field


class ErrorMessageProjectNotFound(BaseModel):
    """Error message for Project not found."""
    
    detail: str = Field(
        default="Project not found",
        examples=["Project not found"]
    )
    error_type: str = Field(
        default="ProjectNotFoundError",
        examples=["ProjectNotFoundError"]
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    detail: str
    error_type: str | None = None
    error_code: str | None = None

    class Config:
        """Pydantic configuration."""
        
        json_schema_extra = {
            "example": {
                "detail": "Project not found",
                "error_type": "ProjectNotFoundError",
                "error_code": "PROJECT_NOT_FOUND"
            }
        }


class ValidationErrorResponse(BaseModel):
    """Validation error response model."""
    
    detail: str
    errors: list[dict] | None = None

    class Config:
        """Pydantic configuration."""
        
        json_schema_extra = {
            "example": {
                "detail": "Validation failed",
                "errors": [
                    {
                        "field": "name",
                        "message": "Field is required"
                    }
                ]
            }
        }
