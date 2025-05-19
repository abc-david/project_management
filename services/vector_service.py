"""
MODULE: modules/project_management/services/vector_service.py
PURPOSE: Handles vector database operations for project management
CLASSES:
    - ProjectVectorService: Manages project vector operations
DEPENDENCIES:
    - chromadb: For vector database operations
    - uuid: For generating IDs
    - logging: For operation logging
    - typing: For type hints
    - json: For serializing data

This module provides vector store services for project management, 
including collection creation, vector storage, and validation.
"""

import uuid
import logging
import json
from typing import Dict, Any, Optional, List, Union

# Set up logging
logger = logging.getLogger(__name__)

class ProjectVectorService:
    """
    Manages vector store operations for projects.
    
    This class handles:
    1. Creating collections for projects
    2. Storing project vectors
    3. Validating vector store setup
    4. Cleaning up failed projects
    """
    
    def __init__(self, client=None, connection_string=None):
        """
        Initialize the vector store service.
        
        Args:
            client: Optional ChromaDB client instance
            connection_string: Optional connection string for ChromaDB
        """
        self.client = client
        self.connection_string = connection_string
        self._initialized = False
    
    async def _initialize(self):
        """Initialize the ChromaDB client if not already initialized."""
        if self._initialized:
            return
        
        try:
            # Import at method level to avoid circular imports
            import chromadb
            
            # Create client if not provided
            if not self.client:
                # Directly create a PersistentClient with minimal dependencies
                persist_dir = "./data/chroma"
                self.client = chromadb.PersistentClient(path=persist_dir)
                
            self._initialized = True
            logger.info("ChromaDB client initialized")
            
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {str(e)}")
            raise
    
    async def create_collection(self, project_id: str, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new collection for the project.
        
        Args:
            project_id: ID of the project
            initial_data: Optional initial data
            
        Returns:
            Collection information
        """
        await self._initialize()
        
        collection_name = f"project_{project_id}"
        
        try:
            # Create collection
            collection = self.client.create_collection(
                name=collection_name,
                metadata={"project_id": project_id}
            )
            
            logger.info(f"Created vector store collection for project: {project_id}")
            
            return {
                "collection_name": collection_name,
                "status": "created"
            }
            
        except Exception as e:
            logger.error(f"Error creating collection for project {project_id}: {str(e)}")
            
            # Check if collection already exists
            try:
                collection = self.client.get_collection(name=collection_name)
                logger.info(f"Collection already exists for project: {project_id}")
                
                return {
                    "collection_name": collection_name,
                    "status": "exists"
                }
            except:
                # Re-raise original error if not just a duplicate collection
                raise
    
    async def store_project_vector(self, project_id: str, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store the project's vector representation.
        
        Args:
            project_id: ID of the project
            project_data: Project data to vectorize
            
        Returns:
            Vector information
        """
        await self._initialize()
        
        collection_name = f"project_{project_id}"
        
        try:
            # Get existing collection
            collection = self.client.get_collection(name=collection_name)
            
            # Generate vector ID
            vector_id = f"project_profile_{project_id}"
            
            # Prepare text for embedding
            project_name = project_data.get("name", "")
            description = project_data.get("description", {})
            settings = project_data.get("settings", {})
            
            # Create a document that summarizes the project
            document_text = f"Project: {project_name}\n"
            
            if description:
                if isinstance(description, dict):
                    for key, value in description.items():
                        document_text += f"{key}: {value}\n"
                else:
                    document_text += f"Description: {description}\n"
            
            if settings:
                if isinstance(settings, dict):
                    document_text += "Settings:\n"
                    for key, value in settings.items():
                        document_text += f"  {key}: {value}\n"
                else:
                    document_text += f"Settings: {settings}\n"
            
            # Store the vector
            collection.add(
                ids=[vector_id],
                documents=[document_text],
                metadatas=[{
                    "project_id": project_id,
                    "type": "project_profile",
                    "name": project_name
                }]
            )
            
            logger.info(f"Stored project vector for project: {project_id}")
            
            return {
                "vector_id": vector_id,
                "status": "stored"
            }
            
        except Exception as e:
            logger.error(f"Error storing project vector for project {project_id}: {str(e)}")
            raise
    
    async def validate_collection(self, project_id: str) -> bool:
        """
        Validate that the collection was created properly.
        
        Args:
            project_id: ID of the project
            
        Returns:
            True if valid, False otherwise
        """
        await self._initialize()
        
        collection_name = f"project_{project_id}"
        vector_id = f"project_profile_{project_id}"
        
        try:
            # Check collection exists
            try:
                collection = self.client.get_collection(name=collection_name)
            except:
                logger.warning(f"Collection not found for project: {project_id}")
                return False
            
            # Check project vector exists
            result = collection.get(ids=[vector_id])
            
            is_valid = len(result["ids"]) > 0
            
            if is_valid:
                logger.info(f"Vector store validation passed for project: {project_id}")
            else:
                logger.warning(f"Vector store validation failed: project vector not found for project: {project_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error validating vector store for project {project_id}: {str(e)}")
            return False
    
    async def remove_collection(self, project_id: str) -> bool:
        """
        Remove a project collection.
        
        Args:
            project_id: ID of the project
            
        Returns:
            True if successful, False otherwise
        """
        await self._initialize()
        
        collection_name = f"project_{project_id}"
        
        try:
            # Delete the collection
            self.client.delete_collection(name=collection_name)
            
            logger.info(f"Removed vector store collection for project: {project_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing collection for project {project_id}: {str(e)}")
            return False 