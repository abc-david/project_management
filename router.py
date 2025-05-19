"""
MODULE: modules/project_management/router.py
PURPOSE: Routes project creation requests to the appropriate orchestrator based on project type
CLASSES:
    - ProjectOrchestratorRouter: Router for project orchestrators
DEPENDENCIES:
    - logging: For operation logging
    - typing: For type hints
    - .orchestrator: For ProjectOrchestrator

This module provides a router system that directs project creation requests
to the appropriate orchestrator based on the project's type. This design
supports different project types while maintaining a consistent interface.
"""

import logging
from typing import Dict, Any, Optional, List, Type

# Import orchestrator
from .orchestrator import ProjectOrchestrator

# Set up logging
logger = logging.getLogger(__name__)

class ProjectOrchestratorRouter:
    """
    Routes project creation requests to the appropriate orchestrator based on project type.
    
    This class acts as a facade over multiple project orchestrators, selecting the
    appropriate implementation based on the project's 'type' attribute. Currently
    supports 'content' type projects via the standard ProjectOrchestrator, with
    extensibility for additional project types in the future.
    """
    
    def __init__(self, db_service, vector_service, template_service):
        """
        Initialize the ProjectOrchestratorRouter.
        
        Args:
            db_service: Service for database operations
            vector_service: Service for vector store operations
            template_service: Service for template operations
        """
        self.db_service = db_service
        self.vector_service = vector_service
        self.template_service = template_service
        
        # Initialize orchestrators map
        self.orchestrators = {}
        
        # Create the default content orchestrator
        self._create_content_orchestrator()
        
    def _create_content_orchestrator(self):
        """Create and register the content project orchestrator."""
        content_orchestrator = ProjectOrchestrator(
            self.db_service,
            self.vector_service,
            self.template_service
        )
        self.orchestrators['content'] = content_orchestrator
        logger.info("Registered content project orchestrator")
    
    def register_orchestrator(self, project_type: str, orchestrator):
        """
        Register a custom orchestrator for a specific project type.
        
        Args:
            project_type: Type of project this orchestrator handles
            orchestrator: Orchestrator instance to handle this project type
        """
        self.orchestrators[project_type] = orchestrator
        logger.info(f"Registered custom orchestrator for project type: {project_type}")
    
    def register_extension(self, extension, project_type: Optional[str] = None):
        """
        Register an extension with the appropriate orchestrator.
        
        Args:
            extension: Extension instance to register
            project_type: Optional project type to register with (defaults to all)
        """
        if project_type:
            if project_type in self.orchestrators:
                self.orchestrators[project_type].register_extension(extension)
                logger.info(f"Registered extension with {project_type} orchestrator: {extension.__class__.__name__}")
            else:
                logger.warning(f"Cannot register extension: no orchestrator for project type {project_type}")
        else:
            # Register with all orchestrators
            for project_type, orchestrator in self.orchestrators.items():
                orchestrator.register_extension(extension)
            logger.info(f"Registered extension with all orchestrators: {extension.__class__.__name__}")
    
    async def create_project(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project by routing to the appropriate orchestrator.
        
        Args:
            project_config: Configuration for the new project, including 'type'
            
        Returns:
            Dict[str, Any]: Project information including ID and status
            
        Raises:
            ValueError: If no orchestrator is available for the specified project type
        """
        # Determine project type, defaulting to 'content'
        project_type = project_config.get('type', 'content')
        
        # Get the appropriate orchestrator
        if project_type not in self.orchestrators:
            error_msg = f"Unsupported project type: {project_type}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        orchestrator = self.orchestrators[project_type]
        logger.info(f"Routing project creation to {project_type} orchestrator")
        
        # Delegate to the orchestrator
        result = await orchestrator.create_project(project_config)
        
        # Add project type to the result
        result['type'] = project_type
        
        return result
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project information by delegating to the standard orchestrator.
        
        Note: Currently, this delegates to the content orchestrator for all projects.
        Future implementations might determine type from the project ID first.
        
        Args:
            project_id: Project ID
            
        Returns:
            Dict[str, Any]: Project information
        """
        # For now, use the content orchestrator for retrieval
        # In future, we could determine type first and route accordingly
        content_orchestrator = self.orchestrators.get('content')
        if not content_orchestrator:
            error_msg = "Content orchestrator not available for project retrieval"
            logger.error(error_msg)
            raise ValueError(error_msg)
            
        return await content_orchestrator.get_project(project_id) 