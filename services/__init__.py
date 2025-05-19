"""
MODULE: modules/project_management/services/__init__.py
PURPOSE: Package for project management services
CLASSES: None (imports from submodules)
DEPENDENCIES: None (imports from submodules)

This package contains services that handle specific aspects of project management:
- DatabaseService: For database operations
- VectorService: For vector store operations
- TemplateService: For template adaptation operations
"""

from .database_service import ProjectDatabaseService
from .vector_service import ProjectVectorService
from .template_service import ProjectTemplateService

__all__ = [
    'ProjectDatabaseService',
    'ProjectVectorService',
    'ProjectTemplateService'
] 