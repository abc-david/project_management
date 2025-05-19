"""
MODULE: modules/project_management/extensions/seo_extension.py
PURPOSE: SEO initialization extension for project management
CLASSES:
    - SEOProjectExtension: Initializes SEO functionality for a project
DEPENDENCIES:
    - modules.project_management.extensions.base: For base extension class
    - modules.seo: For SEO initialization
    - logging: For operation logging
    - typing: For type hints

This module provides an extension for initializing SEO functionality during
project creation. This is an optional step that can be registered with the
project orchestrator.
"""

import logging
from typing import Dict, Any, Optional

from modules.project_management.extensions.base import ProjectExtension

# Set up logging
logger = logging.getLogger(__name__)

class SEOProjectExtension(ProjectExtension):
    """
    Extension for initializing SEO functionality for a project.
    
    This extension handles:
    1. Setting up SEO modules for the project
    2. Bootstrapping initial SEO terrain
    3. Creating vector embeddings for SEO data
    """
    
    def __init__(self, config=None):
        """
        Initialize the SEO extension.
        
        Args:
            config: Optional configuration for SEO initialization
        """
        self.config = config or {}
    
    @property
    def requires_validation(self) -> bool:
        """SEO setup requires validation."""
        return True
    
    async def execute(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize SEO functionality for the project.
        
        Args:
            project_state: Current project state
            
        Returns:
            Dict with SEO initialization results
        """
        try:
            # Extract project information
            project_id = project_state.get("id")
            settings = project_state["config"].get("settings", {})
            
            # Check if SEO initialization is enabled
            if not settings.get("seo_enabled", False):
                logger.info(f"SEO initialization skipped for project {project_id} (not enabled in settings)")
                return {"status": "skipped", "reason": "not_enabled"}
            
            # Import SEO module at runtime to avoid circular dependencies
            from modules.seo import initialize_seo_module
            
            # Get seed topics from settings
            seed_topics = settings.get("seed_topics", [])
            if not seed_topics and "main_topic" in settings:
                seed_topics = [settings["main_topic"]]
            
            if not seed_topics:
                logger.warning(f"No seed topics found for SEO initialization. Using project name.")
                seed_topics = [project_state["config"].get("name", "Default Topic")]
            
            # Configure SEO module
            seo_config = self.config.copy()
            seo_config.update({
                "language": settings.get("language", "en"),
                "location": settings.get("location", "United States"),
                "seed_topics": seed_topics
            })
            
            # Initialize SEO module
            seo_orchestrator = await initialize_seo_module(
                project_id=project_id,
                config=seo_config
            )
            
            # Bootstrap SEO terrain if requested
            if settings.get("bootstrap_seo_terrain", False):
                terrain_result = await seo_orchestrator.bootstrap_terrain(
                    project_id=project_id,
                    seed_topics=seed_topics,
                    location=seo_config["location"],
                    language=seo_config["language"]
                )
                
                # Return success with terrain data
                logger.info(f"SEO terrain bootstrapped for project {project_id} with {len(seed_topics)} seed topics")
                
                return {
                    "status": "completed",
                    "terrain_bootstrapped": True,
                    "keywords_found": len(terrain_result.get("keywords", [])),
                    "opportunities_found": len(terrain_result.get("opportunities", []))
                }
            else:
                # Return success without terrain data
                logger.info(f"SEO module initialized for project {project_id} (terrain bootstrap skipped)")
                
                return {
                    "status": "completed",
                    "terrain_bootstrapped": False
                }
            
        except Exception as e:
            logger.error(f"Error initializing SEO for project: {str(e)}")
            return {"status": "failed", "error": str(e)}
    
    async def validate(self, project_id: str) -> bool:
        """
        Validate SEO initialization.
        
        Args:
            project_id: ID of the project
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Import at method level to avoid circular imports
            from modules.seo import get_seo_orchestrator
            
            # Try to get SEO orchestrator for this project
            seo_orchestrator = get_seo_orchestrator(project_id)
            
            # If we got an orchestrator, then initialization was successful
            is_valid = seo_orchestrator is not None
            
            if is_valid:
                logger.info(f"SEO validation passed for project: {project_id}")
            else:
                logger.warning(f"SEO validation failed: no SEO orchestrator found for project: {project_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating SEO for project {project_id}: {str(e)}")
            return False 