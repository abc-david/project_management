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
        schema_name = await self._generate_schema_name(project_name)
        project_id = str(uuid.uuid4())
        
        # SQL for creating the schema and tables
        create_schema_sql = f"""
        -- Create schema for the project
        CREATE SCHEMA IF NOT EXISTS {schema_name};
        
        -- Create contents table
        CREATE TABLE IF NOT EXISTS {schema_name}.contents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            title VARCHAR(255) NOT NULL,
            content_type VARCHAR(100) NOT NULL,
            data JSONB NOT NULL,
            metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            status VARCHAR(50) NOT NULL DEFAULT 'draft',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        );
        
        -- Create prompts table (simplified from prompt_adaptation)
        CREATE TABLE IF NOT EXISTS {schema_name}.prompts (
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
        CREATE INDEX IF NOT EXISTS {schema_name}_contents_content_type_idx ON {schema_name}.contents(content_type);
        CREATE INDEX IF NOT EXISTS {schema_name}_contents_status_idx ON {schema_name}.contents(status);
        CREATE INDEX IF NOT EXISTS {schema_name}_prompts_name_idx ON {schema_name}.prompts(name);
        CREATE INDEX IF NOT EXISTS {schema_name}_prompts_template_type_idx ON {schema_name}.prompts(template_type);
        CREATE INDEX IF NOT EXISTS {schema_name}_vocabulary_name_idx ON {schema_name}.vocabulary(name);
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
        AND table_name IN ('contents', 'prompts', 'vocabulary')
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
            
            if table_count != 3:
                logger.error(f"Schema validation failed: Expected 3 tables, found {table_count}")
                return False
            
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
    
    async def _schema_exists(self, schema_name: str) -> bool:
        """
        Check if a schema with the given name already exists.
        
        Args:
            schema_name: Schema name to check
            
        Returns:
            True if schema exists, False otherwise
        """
        conn = await self._get_connection()
        
        try:
            # Query information_schema to check if schema exists
            check_schema_sql = """
            SELECT COUNT(*) FROM information_schema.schemata 
            WHERE schema_name = $1
            """
            
            count = await conn.fetchval(check_schema_sql, schema_name)
            return count > 0
        except Exception as e:
            logger.error(f"Error checking if schema exists: {str(e)}")
            raise
        finally:
            await conn.close()
            
    async def _generate_schema_name(self, project_name: str) -> str:
        """
        Generate a safe schema name from project name.
        
        If a schema with the generated name already exists, append a version
        suffix (_v2, _v3, etc.) to ensure uniqueness.
        
        Args:
            project_name: Original project name
            
        Returns:
            Safe and unique schema name
        """
        # Convert to lowercase
        schema_name = project_name.lower()
        
        # Replace spaces and non-alphanumeric chars with underscores
        schema_name = re.sub(r'\W+', '_', schema_name)
        
        # Add prefix
        schema_name = f"proj_{schema_name}"
        
        # Truncate if too long, leaving room for version suffix (PostgreSQL has 63 char limit)
        if len(schema_name) > 55:  # Reduced length to allow for _vN suffix
            schema_name = schema_name[:55]
        
        # Ensure it ends with alphanumeric
        schema_name = re.sub(r'_+$', '', schema_name)
        
        # Check for existing schema with same name
        base_name = schema_name
        version = 2
        
        # Use a while loop to find the first available version
        while await self._schema_exists(schema_name):
            # Schema exists, add version suffix
            schema_name = f"{base_name}_v{version}"
            version += 1
            
            # Edge case: If we exceed PostgreSQL's 63 char limit due to suffix
            if len(schema_name) > 63:
                # Truncate base_name further to make room for suffix
                new_base_length = 62 - len(f"_v{version}")
                base_name = base_name[:new_base_length]
                schema_name = f"{base_name}_v{version}"
        
        return schema_name 