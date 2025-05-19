"""
MODULE: modules/project_management/orchestrator.py
PURPOSE: Provides the central orchestration for project management
CLASSES:
    - ProjectOrchestrator: Coordinates project creation and initialization
DEPENDENCIES:
    - uuid: For generating IDs
    - logging: For operation logging
    - typing: For type hints
    - asyncio: For asynchronous operations

This module defines the central orchestration logic for project management,
coordinating between different services to create and initialize projects.
"""

import uuid
import logging
import asyncio
from typing import Dict, Any, List, Optional, Callable

# Set up logging
logger = logging.getLogger(__name__)

class ProjectOrchestrator:
    """
    Orchestrates the complete project creation and initialization process.
    
    This class coordinates between various services to ensure all aspects of a
    project are properly initialized, including database schema, vector stores,
    and template adaptation.
    """
    
    def __init__(self, db_service, vector_service, template_service):
        """
        Initialize the ProjectOrchestrator.
        
        Args:
            db_service: Service for database operations
            vector_service: Service for vector store operations
            template_service: Service for template operations
        """
        self.db_service = db_service
        self.vector_service = vector_service
        self.template_service = template_service
        self.extensions = []
    
    def register_extension(self, extension):
        """
        Register an extension to the project creation process.
        
        Args:
            extension: Extension instance that implements the execute method
        """
        self.extensions.append(extension)
        logger.info(f"Registered extension: {extension.__class__.__name__}")
    
    async def create_project(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new project with all required components.
        
        This method orchestrates the complete project creation process:
        1. Database schema creation
        2. Vector store initialization
        3. Template adaptation
        4. Extension execution
        5. Final validation
        
        Args:
            project_config: Configuration for the new project
            
        Returns:
            Dict[str, Any]: Project information including ID and status
        """
        # Initialize project state with configuration
        project_state = {
            "config": project_config,
            "status": {
                "database": "pending",
                "vector_store": "pending",
                "templates": "pending",
                "extensions": "pending",
                "validation": "pending"
            },
            "errors": []
        }
        
        logger.info(f"Starting project creation: {project_config.get('name', 'Unnamed project')}")
        
        try:
            # Execute phases in sequence
            project_state = await self._create_database_schema(project_state)
            
            # Only proceed if database creation was successful
            if project_state["status"]["database"] == "completed":
                project_state = await self._initialize_vector_store(project_state)
                project_state = await self._adapt_templates(project_state)
                project_state = await self._run_extensions(project_state)
                project_state = await self._validate_project(project_state)
            
            # Set overall status
            if all(status == "completed" for status in project_state["status"].values()):
                project_state["overall_status"] = "success"
                logger.info(f"Project creation successful: {project_state.get('id')}")
            else:
                project_state["overall_status"] = "partial"
                logger.warning(f"Project creation partially successful: {project_state.get('id')}")
                logger.warning(f"Status details: {project_state['status']}")
                
            return project_state
            
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            project_state["overall_status"] = "failed"
            project_state["errors"].append(str(e))
            
            # Clean up resources if needed
            await self._cleanup_failed_project(project_state)
            
            raise
    
    async def _create_database_schema(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create database schema for the project.
        
        Args:
            project_state: Current project state
            
        Returns:
            Updated project state
        """
        try:
            # Extract project information
            project_config = project_state["config"]
            name = project_config.get("name", "")
            description = project_config.get("description", {})
            settings = project_config.get("settings", {})
            
            # Create database schema
            db_result = await self.db_service.create_schema(name, settings)
            
            # Store project metadata
            project_id = db_result.get("id")
            await self.db_service.store_project_metadata(
                project_id=project_id,
                metadata={
                    "name": name,
                    "description": description,
                    "settings": settings
                }
            )
            
            # Update project state
            project_state["id"] = project_id
            project_state["db_info"] = db_result
            project_state["status"]["database"] = "completed"
            
            logger.info(f"Database schema created for project: {name} (ID: {project_id})")
            return project_state
            
        except Exception as e:
            logger.error(f"Database schema creation failed: {str(e)}")
            project_state["status"]["database"] = "failed"
            project_state["errors"].append(f"Database error: {str(e)}")
            raise
    
    async def _initialize_vector_store(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Initialize vector store for the project.
        
        Args:
            project_state: Current project state
            
        Returns:
            Updated project state
        """
        try:
            # Extract project information
            project_id = project_state.get("id")
            project_config = project_state["config"]
            
            # Prepare project data for vector storage
            project_data = {
                "id": project_id,
                "name": project_config.get("name", ""),
                "description": project_config.get("description", {}),
                "settings": project_config.get("settings", {})
            }
            
            # Create collection
            await self.vector_service.create_collection(project_id)
            
            # Store project vector
            await self.vector_service.store_project_vector(project_id, project_data)
            
            # Update project state
            project_state["status"]["vector_store"] = "completed"
            logger.info(f"Vector store initialized for project: {project_id}")
            
            return project_state
            
        except Exception as e:
            logger.error(f"Vector store initialization failed: {str(e)}")
            project_state["status"]["vector_store"] = "failed"
            project_state["errors"].append(f"Vector store error: {str(e)}")
            
            # Continue with other steps
            return project_state
    
    async def _adapt_templates(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adapt templates for the project.
        
        Args:
            project_state: Current project state
            
        Returns:
            Updated project state
        """
        try:
            # Extract project information
            project_id = project_state.get("id")
            settings = project_state["config"].get("settings", {})
            
            # Adapt templates
            templates_result = await self.template_service.adapt_templates(
                project_id=project_id,
                settings=settings
            )
            
            # Update project state
            project_state["templates_info"] = templates_result
            project_state["status"]["templates"] = "completed"
            
            logger.info(f"Templates adapted for project: {project_id}")
            return project_state
            
        except Exception as e:
            logger.error(f"Template adaptation failed: {str(e)}")
            project_state["status"]["templates"] = "failed"
            project_state["errors"].append(f"Template error: {str(e)}")
            
            # Continue with other steps
            return project_state
    
    async def _run_extensions(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run registered extensions.
        
        Args:
            project_state: Current project state
            
        Returns:
            Updated project state
        """
        if not self.extensions:
            project_state["status"]["extensions"] = "skipped"
            return project_state
            
        try:
            extension_results = {}
            
            # Run each extension
            for extension in self.extensions:
                extension_name = extension.__class__.__name__
                logger.info(f"Running extension: {extension_name}")
                
                try:
                    # Execute the extension
                    extension_result = await extension.execute(project_state)
                    
                    # Store the result
                    extension_results[extension_name] = {
                        "status": "completed",
                        "result": extension_result
                    }
                    
                    logger.info(f"Extension {extension_name} completed")
                    
                except Exception as e:
                    logger.error(f"Extension {extension_name} failed: {str(e)}")
                    extension_results[extension_name] = {
                        "status": "failed",
                        "error": str(e)
                    }
            
            # Update project state
            project_state["extension_results"] = extension_results
            
            # Set overall extension status
            if all(result["status"] == "completed" for result in extension_results.values()):
                project_state["status"]["extensions"] = "completed"
            elif any(result["status"] == "completed" for result in extension_results.values()):
                project_state["status"]["extensions"] = "partial"
            else:
                project_state["status"]["extensions"] = "failed"
                
            return project_state
            
        except Exception as e:
            logger.error(f"Extensions execution failed: {str(e)}")
            project_state["status"]["extensions"] = "failed"
            project_state["errors"].append(f"Extensions error: {str(e)}")
            
            # Continue with other steps
            return project_state
    
    async def _validate_project(self, project_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate all project components.
        
        Args:
            project_state: Current project state
            
        Returns:
            Updated project state
        """
        try:
            project_id = project_state.get("id")
            validation_results = {}
            
            # Validate database schema
            if project_state["status"]["database"] == "completed":
                schema_valid = await self.db_service.validate_schema(project_id)
                validation_results["database"] = schema_valid
            
            # Validate vector store
            if project_state["status"]["vector_store"] == "completed":
                collection_valid = await self.vector_service.validate_collection(project_id)
                validation_results["vector_store"] = collection_valid
            
            # Validate templates
            if project_state["status"]["templates"] == "completed":
                templates_valid = await self.template_service.validate_templates(project_id)
                validation_results["templates"] = templates_valid
            
            # Update project state
            project_state["validation_results"] = validation_results
            
            # Set overall validation status
            if all(validation_results.values()):
                project_state["status"]["validation"] = "completed"
                logger.info(f"Validation successful for project: {project_id}")
            else:
                project_state["status"]["validation"] = "failed"
                failed_components = [k for k, v in validation_results.items() if not v]
                logger.warning(f"Validation failed for components: {failed_components}")
            
            return project_state
            
        except Exception as e:
            logger.error(f"Validation failed: {str(e)}")
            project_state["status"]["validation"] = "failed"
            project_state["errors"].append(f"Validation error: {str(e)}")
            return project_state
    
    async def _cleanup_failed_project(self, project_state: Dict[str, Any]) -> None:
        """
        Clean up resources for a failed project.
        
        Args:
            project_state: Current project state
        """
        project_id = project_state.get("id")
        
        if not project_id:
            logger.info("No cleanup needed - project ID not assigned yet")
            return
            
        cleanup_tasks = []
        
        # Determine which components need cleanup based on status
        if project_state["status"]["database"] == "completed":
            cleanup_tasks.append(self.db_service.remove_schema(project_id))
            
        if project_state["status"]["vector_store"] == "completed":
            cleanup_tasks.append(self.vector_service.remove_collection(project_id))
            
        if project_state["status"]["templates"] == "completed":
            cleanup_tasks.append(self.template_service.remove_templates(project_id))
        
        # Execute cleanup tasks concurrently
        if cleanup_tasks:
            logger.info(f"Cleaning up resources for failed project: {project_id}")
            await asyncio.gather(*cleanup_tasks, return_exceptions=True)
            logger.info("Cleanup completed")
        else:
            logger.info("No cleanup needed")
    
    async def get_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get project information.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project information
        """
        return await self.db_service.get_project(project_id) 