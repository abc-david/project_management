"""
MODULE: modules/project_management/__init__.py
PURPOSE: Provides project management orchestration for the Content Generator
CLASSES: None (exports from sub-modules)
DEPENDENCIES: None (imports from sub-modules)

This module provides centralized project management capabilities including:
1. Project creation and initialization
2. Database schema management
3. Vector store integration
4. Template adaptation
5. Extensible architecture for project-specific customizations

The project management system acts as a coordinator between various services
to ensure a consistent and reliable project setup process.
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

# Import main components for ease of access
from .orchestrator import ProjectOrchestrator
from .router import ProjectOrchestratorRouter
from .services.database_service import ProjectDatabaseService
from .services.vector_service import ProjectVectorService
from .services.template_service import ProjectTemplateService
from .extensions.base import ProjectExtension

__all__ = [
    'ProjectOrchestrator',
    'ProjectOrchestratorRouter',
    'ProjectDatabaseService',
    'ProjectVectorService', 
    'ProjectTemplateService',
    'ProjectExtension',
    'initialize_project_management',
    'create_project'
]

def initialize_project_management(config=None):
    """
    Initialize the project management system.
    
    Args:
        config: Optional configuration dictionary
        
    Returns:
        ProjectOrchestratorRouter instance
    """
    # Initialize services
    db_service = ProjectDatabaseService()
    vector_service = ProjectVectorService()
    template_service = ProjectTemplateService()
    
    # Create router instead of direct orchestrator
    router = ProjectOrchestratorRouter(
        db_service=db_service,
        vector_service=vector_service,
        template_service=template_service
    )
    
    logger.info("Project management system initialized with router")
    return router

async def create_project(name, description=None, settings=None, extensions=None, project_type='content'):
    """
    Convenience function to create a new project.
    
    Args:
        name: Project name
        description: Project description dictionary
        settings: Project settings dictionary
        extensions: List of ProjectExtension instances
        project_type: Type of project to create (default: 'content')
        
    Returns:
        Project information
    """
    router = initialize_project_management()
    
    # Register extensions if provided
    if extensions:
        for extension in extensions:
            router.register_extension(extension)
    
    # Create project configuration
    project_config = {
        "name": name,
        "description": description or {},
        "settings": settings or {},
        "type": project_type
    }
    
    # Create the project
    result = await router.create_project(project_config)
    logger.info(f"{project_type.capitalize()} project created: {name} (ID: {result['id']})")
    
    return result 