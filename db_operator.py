"""
MODULE: modules/project_management/db_operator.py
PURPOSE: Database operations for project management
CLASSES:
    - DBOperator: Handles all project-related database operations
DEPENDENCIES:
    - services.database.db_connector: For PostgreSQL database connection
    - uuid: For UUID generation
    - json: For JSON serialization/deserialization
    - datetime: For timestamp handling
    - logging: For operation logging

This module provides database operations for the project management functionality,
including creating, updating, and retrieving projects.
"""

import json
import uuid
import logging
from typing import Dict, List, Optional, Union, Any, Literal
from datetime import datetime

# Import database connector
from services.database.db_connector import DBConnector, with_db_connection

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define project type literal for type checking
ProjectType = Literal['content', 'seo', 'chatbot']

class DBOperator:
    """
    Database operator for project management.
    
    Handles all database operations related to projects, including creation,
    retrieval, and updates.
    """
    
    def __init__(self):
        """Initialize the database operator."""
        self.db = DBConnector()
    
    def create_project(self, 
                      name: str, 
                      schema_name: str, 
                      description: Dict[str, Any],
                      primary_language: str = 'en',
                      project_type: ProjectType = 'content',
                      created_by: Optional[str] = None,
                      parent_project_id: Optional[str] = None,
                      is_template: bool = False,
                      status: str = 'draft') -> str:
        """
        Create a new project in the database.
        
        Args:
            name: Project name
            schema_name: Database schema name
            description: Project description as a dictionary (will be stored as JSONB)
            primary_language: Primary language code
            project_type: Type of project ('content', 'seo', 'chatbot')
            created_by: UUID of user creating the project
            parent_project_id: UUID of parent project (optional)
            is_template: Whether this project is a template
            status: Project status
            
        Returns:
            The UUID of the newly created project
        """
        # Validate description structure
        if not isinstance(description, dict):
            raise ValueError("Description must be a dictionary")
            
        # Ensure required keys exist in description
        if "metadata" not in description:
            description["metadata"] = {}
        if "content" not in description:
            description["content"] = {}
            
        # Validate project type
        if project_type not in ('content', 'seo', 'chatbot'):
            raise ValueError("project_type must be one of: 'content', 'seo', 'chatbot'")
            
        # Generate a new UUID for the project
        project_id = str(uuid.uuid4())
        
        # Insert the project
        try:
            self.db.insert(
                "projects",
                {
                    "id": project_id,
                    "name": name,
                    "schema_name": schema_name,
                    "description": json.dumps(description),
                    "primary_language": primary_language,
                    "project_type": project_type,
                    "created_by": created_by,
                    "parent_project_id": parent_project_id,
                    "is_template": is_template,
                    "status": status,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                },
                schema="public"
            )
            logger.info(f"Created project: {name} (ID: {project_id}, Type: {project_type})")
            return project_id
        except Exception as e:
            logger.error(f"Error creating project: {str(e)}")
            raise
    
    def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a project by ID.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            Project data as a dictionary, or None if not found
        """
        try:
            result = self.db.execute_query(
                """
                SELECT id, name, schema_name, description, created_by, 
                created_at, updated_at, primary_language, status,
                project_type, vector_collection_id, parent_project_id, is_template
                FROM public.projects WHERE id = %s
                """,
                (project_id,)
            )
            
            if not result:
                logger.warning(f"Project not found: {project_id}")
                return None
                
            # Process the row into a dictionary
            columns = [
                "id", "name", "schema_name", "description", "created_by", 
                "created_at", "updated_at", "primary_language", "status",
                "project_type", "vector_collection_id", "parent_project_id", "is_template"
            ]
            
            project_data = dict(zip(columns, result[0]))
            
            # Parse JSONB data - handle different types of description values
            if project_data.get("description"):
                try:
                    # If it's already a dict, no need to parse
                    if isinstance(project_data["description"], dict):
                        pass
                    # Handle string representation of JSON
                    elif isinstance(project_data["description"], str):
                        project_data["description"] = json.loads(project_data["description"])
                    # PostgreSQL might return a specialized type
                    else:
                        project_data["description"] = json.loads(str(project_data["description"]))
                except Exception as e:
                    logger.error(f"Error parsing project description JSON: {str(e)}")
                    # If JSON parsing fails, keep the description as is
                    pass
                
            return project_data
        except Exception as e:
            logger.error(f"Error retrieving project: {str(e)}")
            raise
    
    def update_project(self, project_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a project.
        
        Args:
            project_id: UUID of the project
            update_data: Dictionary of fields to update
            
        Returns:
            True if successful, False if project not found
        """
        try:
            # Check if the project exists
            project = self.get_project(project_id)
            if not project:
                logger.warning(f"Cannot update, project not found: {project_id}")
                return False
                
            # Validate project_type if it's being updated
            if "project_type" in update_data and update_data["project_type"] not in ('content', 'seo', 'chatbot'):
                raise ValueError("project_type must be one of: 'content', 'seo', 'chatbot'")
                
            # Handle description updates specially
            if "description" in update_data and isinstance(update_data["description"], dict):
                current_description = project.get("description", {})
                
                # If current_description is not a dict, initialize it
                if not isinstance(current_description, dict):
                    current_description = {}
                
                # If updating specific keys in the description
                for key, value in update_data["description"].items():
                    if isinstance(value, dict) and key in current_description and isinstance(current_description[key], dict):
                        # Merge nested dictionaries
                        current_description[key].update(value)
                    else:
                        # Replace or add the key
                        current_description[key] = value
                        
                # Replace the update_data description with the merged result
                update_data["description"] = json.dumps(current_description)
            
            # Update the project
            result = self.db.update(
                "projects",
                update_data,
                {"id": project_id},
                schema="public"
            )
            
            logger.info(f"Updated project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating project: {str(e)}")
            raise
    
    def delete_project(self, project_id: str) -> bool:
        """
        Delete a project.
        
        Args:
            project_id: UUID of the project
            
        Returns:
            True if successful, False if project not found
        """
        try:
            # Check if the project exists
            project = self.get_project(project_id)
            if not project:
                logger.warning(f"Cannot delete, project not found: {project_id}")
                return False
                
            # Delete the project
            self.db.execute_query(
                """
                DELETE FROM public.projects WHERE id = %s
                """,
                (project_id,)
            )
            
            logger.info(f"Deleted project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting project: {str(e)}")
            raise
    
    def list_projects(self, 
                     status: Optional[str] = None, 
                     primary_language: Optional[str] = None,
                     project_type: Optional[ProjectType] = None,
                     is_template: Optional[bool] = None,
                     limit: int = 100,
                     offset: int = 0) -> List[Dict[str, Any]]:
        """
        List projects with optional filtering.
        
        Args:
            status: Filter by status (optional)
            primary_language: Filter by primary language (optional)
            project_type: Filter by project type (optional)
            is_template: Filter by template flag (optional)
            limit: Maximum number of projects to return
            offset: Offset for pagination
            
        Returns:
            List of project data dictionaries
        """
        try:
            # Build the query based on filters
            query = """
            SELECT id, name, schema_name, description, created_by, 
            created_at, updated_at, primary_language, status,
            project_type, vector_collection_id, parent_project_id, is_template
            FROM public.projects WHERE 1=1
            """
            params = []
            
            if status:
                query += " AND status = %s"
                params.append(status)
                
            if primary_language:
                query += " AND primary_language = %s"
                params.append(primary_language)
                
            if project_type:
                query += " AND project_type = %s"
                params.append(project_type)
                
            if is_template is not None:
                query += " AND is_template = %s"
                params.append(is_template)
                
            # Add ordering and pagination
            query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
            
            # Execute the query
            results = self.db.execute_query(query, tuple(params))
            
            if not results:
                return []
                
            # Process the rows into dictionaries
            columns = [
                "id", "name", "schema_name", "description", "created_by", 
                "created_at", "updated_at", "primary_language", "status",
                "project_type", "vector_collection_id", "parent_project_id", "is_template"
            ]
            
            projects = []
            for row in results:
                project_data = dict(zip(columns, row))
                
                # Parse JSONB data
                if project_data.get("description"):
                    try:
                        # If it's already a dict, no need to parse
                        if isinstance(project_data["description"], dict):
                            pass
                        # Handle string representation of JSON
                        elif isinstance(project_data["description"], str):
                            project_data["description"] = json.loads(project_data["description"])
                        # PostgreSQL might return a specialized type
                        else:
                            project_data["description"] = json.loads(str(project_data["description"]))
                    except Exception as e:
                        logger.error(f"Error parsing project description JSON: {str(e)}")
                        # If JSON parsing fails, keep the description as is
                        pass
                    
                projects.append(project_data)
                
            return projects
        except Exception as e:
            logger.error(f"Error listing projects: {str(e)}")
            raise
    
    def search_projects_by_tag(self, tag: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for projects by tag.
        
        Args:
            tag: The tag to search for
            limit: Maximum number of projects to return
            
        Returns:
            List of matching project data dictionaries
        """
        try:
            # Use the JSONB tag index for efficient searching
            query = """
            SELECT id, name, schema_name, description, created_by, 
            created_at, updated_at, primary_language, status,
            project_type, vector_collection_id, parent_project_id, is_template
            FROM public.projects 
            WHERE description->'metadata'->'tags' ? %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            
            results = self.db.execute_query(query, (tag, limit))
            
            if not results:
                return []
                
            # Process the rows into dictionaries
            columns = [
                "id", "name", "schema_name", "description", "created_by", 
                "created_at", "updated_at", "primary_language", "status",
                "project_type", "vector_collection_id", "parent_project_id", "is_template"
            ]
            
            projects = []
            for row in results:
                project_data = dict(zip(columns, row))
                
                # Parse JSONB data
                if project_data.get("description"):
                    try:
                        # If it's already a dict, no need to parse
                        if isinstance(project_data["description"], dict):
                            pass
                        # Handle string representation of JSON
                        elif isinstance(project_data["description"], str):
                            project_data["description"] = json.loads(project_data["description"])
                        # PostgreSQL might return a specialized type
                        else:
                            project_data["description"] = json.loads(str(project_data["description"]))
                    except Exception as e:
                        logger.error(f"Error parsing project description JSON: {str(e)}")
                        # If JSON parsing fails, keep the description as is
                        pass
                    
                projects.append(project_data)
                
            return projects
        except Exception as e:
            logger.error(f"Error searching projects by tag: {str(e)}")
            raise
    
    def search_projects_by_industry(self, industry: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Search for projects by industry.
        
        Args:
            industry: The industry to search for
            limit: Maximum number of projects to return
            
        Returns:
            List of matching project data dictionaries
        """
        try:
            # Use the JSONB industry index for efficient searching
            query = """
            SELECT id, name, schema_name, description, created_by, 
            created_at, updated_at, primary_language, status,
            project_type, vector_collection_id, parent_project_id, is_template
            FROM public.projects 
            WHERE description->'content'->>'industry' = %s
            ORDER BY created_at DESC
            LIMIT %s
            """
            
            results = self.db.execute_query(query, (industry, limit))
            
            if not results:
                return []
                
            # Process the rows into dictionaries
            columns = [
                "id", "name", "schema_name", "description", "created_by", 
                "created_at", "updated_at", "primary_language", "status",
                "project_type", "vector_collection_id", "parent_project_id", "is_template"
            ]
            
            projects = []
            for row in results:
                project_data = dict(zip(columns, row))
                
                # Parse JSONB data
                if project_data.get("description"):
                    try:
                        # If it's already a dict, no need to parse
                        if isinstance(project_data["description"], dict):
                            pass
                        # Handle string representation of JSON
                        elif isinstance(project_data["description"], str):
                            project_data["description"] = json.loads(project_data["description"])
                        # PostgreSQL might return a specialized type
                        else:
                            project_data["description"] = json.loads(str(project_data["description"]))
                    except Exception as e:
                        logger.error(f"Error parsing project description JSON: {str(e)}")
                        # If JSON parsing fails, keep the description as is
                        pass
                    
                projects.append(project_data)
                
            return projects
        except Exception as e:
            logger.error(f"Error searching projects by industry: {str(e)}")
            raise
    
    def update_project_status(self, project_id: str, status: str) -> bool:
        """
        Update a project's status.
        
        Args:
            project_id: UUID of the project
            status: New status value
            
        Returns:
            True if successful, False if project not found
        """
        return self.update_project(project_id, {"status": status})
    
    def update_project_type(self, project_id: str, project_type: ProjectType) -> bool:
        """
        Update a project's type.
        
        Args:
            project_id: UUID of the project
            project_type: New project type ('content', 'seo', 'chatbot')
            
        Returns:
            True if successful, False if project not found
        """
        if project_type not in ('content', 'seo', 'chatbot'):
            raise ValueError("project_type must be one of: 'content', 'seo', 'chatbot'")
            
        return self.update_project(project_id, {"project_type": project_type})
    
    def update_project_description(self, project_id: str, 
                                  description_updates: Dict[str, Any]) -> bool:
        """
        Update specific parts of a project's description.
        
        Args:
            project_id: UUID of the project
            description_updates: Dictionary of updates to apply to the description
            
        Returns:
            True if successful, False if project not found
        """
        return self.update_project(project_id, {"description": description_updates})
    
    def set_vector_collection_id(self, project_id: str, 
                               vector_collection_id: str) -> bool:
        """
        Set the vector collection ID for a project.
        
        Args:
            project_id: UUID of the project
            vector_collection_id: ID of the vector collection
            
        Returns:
            True if successful, False if project not found
        """
        return self.update_project(
            project_id, 
            {"vector_collection_id": vector_collection_id}
        )
        
    def get_projects_by_type(self, project_type: ProjectType, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get projects by type.
        
        Args:
            project_type: The project type to filter by
            limit: Maximum number of projects to return
            
        Returns:
            List of matching project data dictionaries
        """
        return self.list_projects(project_type=project_type, limit=limit) 