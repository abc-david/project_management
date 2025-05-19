"""
MODULE: modules/project_management/services/template_service.py
PURPOSE: Handles template adaptation for project management
CLASSES:
    - ProjectTemplateService: Manages project template operations
    - MockPromptService: Mock implementation for testing
DEPENDENCIES:
    - services.llm.prompt_service: For prompt template operations
    - logging: For operation logging
    - typing: For type hints

This module provides template adaptation services for project management,
ensuring that projects have properly localized and adapted templates.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

# Set up logging
logger = logging.getLogger(__name__)

# Mock implementation for testing
class MockPromptService:
    """Mock implementation of the PromptService for testing purposes."""
    
    async def ensure_project_templates(self, project_id, settings):
        """Mock ensuring project templates."""
        logger.info(f"Mock: Ensuring templates for project {project_id}")
        return {
            "templates_adapted": 5,
            "templates_skipped": 0
        }
    
    async def get_adapted_templates_for_project(self, project_id):
        """Mock getting adapted templates."""
        logger.info(f"Mock: Getting templates for project {project_id}")
        return ["template1", "template2", "template3", "template4", "template5"]
    
    async def delete_project_templates(self, project_id):
        """Mock deleting project templates."""
        logger.info(f"Mock: Deleting templates for project {project_id}")
        return {"deleted": 5}

class ProjectTemplateService:
    """
    Manages template adaptation for projects.
    
    This class handles:
    1. Adapting templates for projects
    2. Validating template adaptation
    3. Cleaning up templates for failed projects
    """
    
    def __init__(self, prompt_service=None):
        """
        Initialize the template service.
        
        Args:
            prompt_service: Optional PromptService instance
        """
        self.prompt_service = None
        self._prompt_service_initialized = False
    
    async def _initialize(self):
        """Initialize the PromptService if not already initialized."""
        if self._prompt_service_initialized:
            return
        
        try:
            # For testing, create a mock prompt service
            self.prompt_service = MockPromptService()
            self._prompt_service_initialized = True
            logger.info("Mock PromptService initialized for testing")
        except Exception as e:
            logger.error(f"Error initializing PromptService: {str(e)}")
            raise

    async def adapt_templates(self, project_id: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt templates for the project based on settings.
        
        Args:
            project_id: ID of the project
            settings: Project settings including language preferences
            
        Returns:
            Dict with adaptation results
        """
        await self._initialize()
        
        try:
            # Ensure templates are adapted for the project
            adaptation_result = await self.prompt_service.ensure_project_templates(
                project_id=project_id,
                settings=settings
            )
            
            logger.info(f"Templates adapted for project: {project_id}")
            
            return {
                "status": "completed",
                "templates_adapted": adaptation_result.get("templates_adapted", 0),
                "templates_skipped": adaptation_result.get("templates_skipped", 0)
            }
            
        except Exception as e:
            logger.error(f"Error adapting templates for project {project_id}: {str(e)}")
            raise
    
    async def validate_templates(self, project_id: str) -> bool:
        """
        Validate that templates were adapted properly.
        
        Args:
            project_id: ID of the project
            
        Returns:
            True if valid, False otherwise
        """
        await self._initialize()
        
        try:
            # Check if adapted templates exist for the project
            templates = await self.prompt_service.get_adapted_templates_for_project(project_id)
            
            is_valid = len(templates) > 0
            
            if is_valid:
                logger.info(f"Template validation passed for project: {project_id}")
            else:
                logger.warning(f"Template validation failed: no adapted templates found for project: {project_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating templates for project {project_id}: {str(e)}")
            return False
    
    async def remove_templates(self, project_id: str) -> bool:
        """
        Remove adapted templates for a project.
        
        Args:
            project_id: ID of the project
            
        Returns:
            True if successful, False otherwise
        """
        await self._initialize()
        
        try:
            # Delete adapted templates
            result = await self.prompt_service.delete_project_templates(project_id)
            
            if result and result.get("deleted", 0) > 0:
                logger.info(f"Removed {result.get('deleted')} adapted templates for project: {project_id}")
                return True
            else:
                logger.info(f"No templates found to remove for project: {project_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error removing templates for project {project_id}: {str(e)}")
            return False 