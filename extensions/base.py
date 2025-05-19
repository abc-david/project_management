"""
MODULE: modules/project_management/extensions/base.py
PURPOSE: Provides the base class for project extensions
CLASSES:
    - ProjectExtension: Abstract base class for project creation extensions
DEPENDENCIES:
    - abc: For abstract base class functionality
    - typing: For type hints

This module defines the abstract base class that all project extensions must implement.
Extensions provide a way to customize the project creation process with optional
functionality like SEO initialization, permissions setup, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any

class ProjectExtension(ABC):
    """
    Abstract base class for project extensions.
    
    Project extensions allow for customizing the project creation process
    with additional functionality beyond the core setup steps.
    
    Examples include:
    - SEO initialization
    - Permissions and access control setup
    - Integration with external systems
    - Specialized data initialization
    """
    
    @property
    def name(self) -> str:
        """Get the extension name."""
        return self.__class__.__name__
    
    @abstractmethod
    async def execute(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the extension's functionality.
        
        This method should perform the extension's specific functionality
        and return any relevant results to be incorporated into the project state.
        
        Args:
            project_state: Current state of the project creation process
            
        Returns:
            Dict containing the extension's results
        """
        pass
    
    @property
    def requires_validation(self) -> bool:
        """
        Whether this extension requires validation after project creation.
        
        Returns:
            True if validation is required, False otherwise
        """
        return False
    
    async def validate(self, project_id: str) -> bool:
        """
        Validate the extension's setup for a project.
        
        Args:
            project_id: ID of the project to validate
            
        Returns:
            True if validation passed, False otherwise
        """
        return True 