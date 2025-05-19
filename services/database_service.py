"""
MODULE: modules/project_management/services/database_service.py
PURPOSE: Handles database operations for project management
CLASSES:
    - ProjectDatabaseService: Manages project database operations
DEPENDENCIES:
    - asyncpg: For PostgreSQL database operations
    - uuid: For generating IDs
    - logging: For operation logging
    - typing: For type hints
    - re: For schema name formatting

This module provides database services for project management, including
schema creation, metadata storage, and validation.
"""

import uuid
import logging
import re
import json
from typing import Dict, Any, Optional, List, Tuple
import asyncio
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

class ProjectDatabaseService:
    """
    Manages database operations for projects.
    
    This class handles:
    1. Creating project schemas
    2. Storing project metadata
    3. Validating database setup
    4. Cleaning up failed projects
    """
    
    def __init__(self, connection_string: Optional[str] = None):
        """
        Initialize the database service.
        
        Args:
            connection_string: Optional database connection string
        """
        # Import at method level to avoid circular imports
        from config.settings import get_db_connection_string
        
        self.connection_string = connection_string or get_db_connection_string()
    
    async def _get_connection(self):
        """Get a database connection."""
        # Import here to avoid top-level import issues
        import asyncpg
        from config.settings import DB_CONNECT
        
        # Use directly from settings instead of connection string
        return await asyncpg.connect(
            user=DB_CONNECT["user"],
            password=DB_CONNECT["password"],
            database=DB_CONNECT["dbname"],
            host=DB_CONNECT["host"],
            port=DB_CONNECT["port"]
        )
    
    async def create_schema(self, project_name: str, settings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new schema for the project and initialize tables.
        
        Args:
            project_name: Name of the project
            settings: Project settings
            
        Returns:
            Dict with project ID and schema info
        """
        # Generate a safe schema name
        schema_name = self._generate_schema_name(project_name)
        project_id = str(uuid.uuid4())
        
        # SQL for creating the schema and tables
        create_schema_sql = f"""
        -- Create schema for the project
        CREATE SCHEMA IF NOT EXISTS {schema_name};
        
        -- Create object_models table
        CREATE TABLE IF NOT EXISTS {schema_name}.object_models (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            version VARCHAR(20) NOT NULL DEFAULT '1.0',
            definition JSONB NOT NULL,
            object_type VARCHAR(50) NOT NULL,
            description TEXT NOT NULL,
            use_cases TEXT[] NOT NULL DEFAULT '{{}}',
            related_models TEXT[] NOT NULL DEFAULT '{{}}',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create contents table
        CREATE TABLE IF NOT EXISTS {schema_name}.contents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(255) NOT NULL,
            content_type VARCHAR(100) NOT NULL,
            object_model_id UUID REFERENCES {schema_name}.object_models(id),
            data JSONB NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create prompt_adaptation table
        CREATE TABLE IF NOT EXISTS {schema_name}.prompt_adaptation (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            engine_type VARCHAR(50) NOT NULL,
            template_type VARCHAR(50) NOT NULL,
            template JSONB NOT NULL,
            description TEXT NOT NULL,
            use_cases TEXT[] NOT NULL DEFAULT '{{}}',
            version VARCHAR(20) NOT NULL DEFAULT '1.0',
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        -- Create prompt_history table
        CREATE TABLE IF NOT EXISTS {schema_name}.prompt_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            template_id UUID REFERENCES {schema_name}.prompt_adaptation(id),
            input_variables JSONB NOT NULL,
            full_prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            operation_name VARCHAR(100) NULL,
            content_id UUID REFERENCES {schema_name}.contents(id),
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );
        
        -- Create vocabulary table
        CREATE TABLE IF NOT EXISTS {schema_name}.vocabulary (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            name VARCHAR(100) NOT NULL UNIQUE,
            values JSONB NOT NULL,
            description TEXT NOT NULL,
            is_system BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create indexes
        CREATE INDEX IF NOT EXISTS {schema_name}_object_models_name_idx ON {schema_name}.object_models(name);
        CREATE INDEX IF NOT EXISTS {schema_name}_object_models_object_type_idx ON {schema_name}.object_models(object_type);
        CREATE INDEX IF NOT EXISTS {schema_name}_contents_content_type_idx ON {schema_name}.contents(content_type);
        CREATE INDEX IF NOT EXISTS {schema_name}_contents_status_idx ON {schema_name}.contents(status);
        CREATE INDEX IF NOT EXISTS {schema_name}_prompt_templates_name_idx ON {schema_name}.prompt_adaptation(name);
        CREATE INDEX IF NOT EXISTS {schema_name}_prompt_templates_template_type_idx ON {schema_name}.prompt_adaptation(template_type);
        CREATE INDEX IF NOT EXISTS {schema_name}_prompt_history_template_id_idx ON {schema_name}.prompt_history(template_id);
        CREATE INDEX IF NOT EXISTS {schema_name}_prompt_history_created_at_idx ON {schema_name}.prompt_history(created_at);
        CREATE INDEX IF NOT EXISTS {schema_name}_vocabulary_name_idx ON {schema_name}.vocabulary(name);
        
        -- Copy object model templates from public schema
        INSERT INTO {schema_name}.object_models (
            name, version, definition, object_type, description, use_cases, created_at, updated_at
        )
        SELECT 
            name, version, definition, object_type, description, use_cases, created_at, updated_at
        FROM 
            public.object_model_templates;
        """
        
        # Store settings in the description field since there's no settings column
        description = {
            "settings": settings,
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "schema_version": "1.0"
            }
        }
        
        # Create public projects entry SQL
        create_project_sql = """
        INSERT INTO public.projects(
            id, name, schema_name, description, 
            primary_language, created_at, updated_at
        )
        VALUES($1, $2, $3, $4, $5, NOW(), NOW())
        RETURNING id, name, schema_name
        """
        
        conn = await self._get_connection()
        
        try:
            # Begin transaction
            async with conn.transaction():
                # Create the schema and tables
                await conn.execute(create_schema_sql)
                
                # Create the project entry
                primary_language = settings.get("language", "en")
                
                project_record = await conn.fetchrow(
                    create_project_sql,
                    project_id,
                    project_name,
                    schema_name,
                    json.dumps(description),
                    primary_language
                )
                
                # Convert to dictionary
                project_info = dict(project_record)
                
                logger.info(f"Created database schema for project: {project_name} (ID: {project_id})")
                
                return {
                    "id": project_info["id"],
                    "name": project_info["name"],
                    "schema_name": project_info["schema_name"]
                }
        except Exception as e:
            logger.error(f"Error creating schema for project {project_name}: {str(e)}")
            raise
        finally:
            await conn.close()
    
    async def store_project_metadata(self, project_id: str, metadata: Dict[str, Any]) -> None:
        """
        Store or update project metadata.
        
        Args:
            project_id: Project ID
            metadata: Project metadata including name, description, settings
        """
        # First get current description 
        get_current_desc_sql = """
        SELECT description FROM public.projects WHERE id = $1
        """
        
        # Then update with merged data
        update_sql = """
        UPDATE public.projects
        SET description = $1::jsonb,
            updated_at = NOW()
        WHERE id = $2
        """
        
        conn = await self._get_connection()
        
        try:
            # Get current description
            current_desc_json = await conn.fetchval(get_current_desc_sql, project_id)
            
            try:
                if current_desc_json:
                    current_desc = json.loads(current_desc_json)
                else:
                    current_desc = {}
            except:
                # If we can't parse, start fresh
                current_desc = {}
            
            # Extract metadata components
            settings = metadata.get("settings", {})
            new_metadata = metadata.get("metadata", {})
            
            # Update the description object
            if settings:
                current_desc["settings"] = settings
            if new_metadata:
                if "metadata" not in current_desc:
                    current_desc["metadata"] = {}
                current_desc["metadata"].update(new_metadata)
            
            # Execute update
            await conn.execute(
                update_sql,
                json.dumps(current_desc),
                project_id
            )
            
            logger.info(f"Updated metadata for project: {project_id}")
        except Exception as e:
            logger.error(f"Error updating metadata for project {project_id}: {str(e)}")
            raise
        finally:
            await conn.close()
    
    async def validate_schema(self, project_id: str) -> bool:
        """
        Validate that the schema was created properly.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if valid, False otherwise
        """
        # Get schema name from project ID
        get_schema_sql = """
        SELECT schema_name FROM public.projects WHERE id = $1
        """
        
        # Check if all required tables exist
        check_tables_sql = """
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = $1
        AND table_name IN ('object_models', 'contents', 'prompt_adaptation', 'prompt_history', 'vocabulary')
        """
        
        # Check if object_models were copied correctly
        check_models_sql = """
        SELECT COUNT(*) FROM {}.object_models
        """
        
        conn = await self._get_connection()
        
        try:
            # Get schema name
            schema_name = await conn.fetchval(get_schema_sql, project_id)
            
            if not schema_name:
                logger.error(f"Project not found: {project_id}")
                return False
            
            # Check tables
            table_count = await conn.fetchval(check_tables_sql, schema_name)
            
            if table_count != 5:
                logger.error(f"Schema validation failed: Expected 5 tables, found {table_count}")
                return False
            
            # Check if object models were copied
            models_count = await conn.fetchval(check_models_sql.format(schema_name))
            
            if models_count == 0:
                logger.warning(f"Schema validation warning: No object models found in {schema_name}")
            
            # If we got here, the schema is valid
            logger.info(f"Schema validation successful for project: {project_id}")
            return True
        except Exception as e:
            logger.error(f"Error validating schema for project {project_id}: {str(e)}")
            return False
        finally:
            await conn.close()
    
    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Get project information.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project information or None if not found
        """
        query = """
        SELECT id, name, schema_name, description,
               created_at, updated_at, primary_language, status, project_type,
               vector_collection_id, parent_project_id, is_template
        FROM public.projects
        WHERE id = $1
        """
        
        conn = await self._get_connection()
        
        try:
            # Execute query
            row = await conn.fetchrow(query, project_id)
            
            if not row:
                return None
            
            # Convert to dictionary
            project_info = dict(row)
            
            # Parse JSON fields
            project_info["description"] = json.loads(project_info["description"])
            
            # Add settings as empty dict (for compatibility)
            project_info["settings"] = {}
            
            return project_info
            
        except Exception as e:
            logger.error(f"Error getting project {project_id}: {str(e)}")
            raise
        finally:
            await conn.close()
    
    async def remove_schema(self, project_id: str) -> bool:
        """
        Remove a project schema and its entry.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if successful, False otherwise
        """
        # SQL to get schema name and remove project
        get_schema_sql = """
        SELECT schema_name FROM public.projects WHERE id = $1
        """
        
        remove_project_sql = """
        DELETE FROM public.projects WHERE id = $1
        """
        
        conn = await self._get_connection()
        
        try:
            # Begin transaction
            async with conn.transaction():
                # Get schema name
                schema_name = await conn.fetchval(get_schema_sql, project_id)
                
                if not schema_name:
                    logger.warning(f"Schema not found for project: {project_id}")
                    return False
                
                # Drop schema
                drop_schema_sql = f"DROP SCHEMA IF EXISTS {schema_name} CASCADE"
                await conn.execute(drop_schema_sql)
                
                # Remove project entry
                await conn.execute(remove_project_sql, project_id)
                
                logger.info(f"Removed schema and project entry for project: {project_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error removing schema for project {project_id}: {str(e)}")
            return False
        finally:
            await conn.close()
    
    def _generate_schema_name(self, project_name: str) -> str:
        """
        Generate a safe schema name from project name.
        
        Args:
            project_name: Original project name
            
        Returns:
            Safe schema name
        """
        # Convert to lowercase
        schema_name = project_name.lower()
        
        # Replace spaces and non-alphanumeric chars with underscores
        schema_name = re.sub(r'\W+', '_', schema_name)
        
        # Add prefix
        schema_name = f"proj_{schema_name}"
        
        # Truncate if too long (PostgreSQL has 63 char limit for identifiers)
        if len(schema_name) > 60:
            schema_name = schema_name[:60]
        
        # Ensure it ends with alphanumeric
        schema_name = re.sub(r'_+$', '', schema_name)
        
        return schema_name 