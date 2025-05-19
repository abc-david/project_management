"""
MODULE: modules/project_management/tests/unit/test_database_service.py
PURPOSE: Unit tests for project database service
CLASSES:
    - TestProjectDatabaseService: Tests database service operations
DEPENDENCIES:
    - pytest: For test assertions and fixtures
    - unittest.mock: For mocking database connections
    - modules.project_management.services.database_service: Module under test

This module provides unit tests for the ProjectDatabaseService class,
ensuring proper schema creation, metadata storage, and validation.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call

from modules.project_management.services.database_service import ProjectDatabaseService


@pytest.mark.asyncio
async def test_init():
    """Test service initialization with different parameters."""
    # Test with default connection string
    with patch('config.settings.get_db_connection_string', 
               return_value="postgresql://test:test@localhost:5432/test_db"):
        service = ProjectDatabaseService()
        assert service.connection_string == "postgresql://test:test@localhost:5432/test_db"
    
    # Test with custom connection string
    custom_conn = "postgresql://custom:custom@localhost:5432/custom_db"
    service = ProjectDatabaseService(connection_string=custom_conn)
    assert service.connection_string == custom_conn


@pytest.mark.asyncio
async def test_create_schema():
    """Test schema creation for a project."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection and transaction
    mock_conn = AsyncMock()
    mock_conn.transaction = MagicMock()
    mock_conn.transaction.return_value.__aenter__ = AsyncMock()
    mock_conn.transaction.return_value.__aexit__ = AsyncMock()
    
    # Mock fetchrow to return a result
    mock_conn.fetchrow.return_value = {
        "id": "test-id",
        "name": "Test Project",
        "schema_name": "test_project"
    }
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call create_schema
        result = await service.create_schema(
            project_name="Test Project", 
            settings={"language": "en"}
        )
        
        # Verify the result
        assert result is not None
        assert "id" in result
        assert "name" in result
        assert "schema_name" in result
        assert result["id"] == "test-id"
        assert result["name"] == "Test Project"
        
        # Verify execute was called with SQL that contains CREATE SCHEMA
        args, kwargs = mock_conn.execute.call_args
        sql = args[0]
        assert "CREATE SCHEMA" in sql
        assert "CREATE TABLE" in sql
        
        # Verify fetchrow was called with INSERT
        args, kwargs = mock_conn.fetchrow.call_args
        sql = args[0]
        assert "INSERT INTO public.projects" in sql


@pytest.mark.asyncio
async def test_store_project_metadata():
    """Test storing project metadata."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection
    mock_conn = AsyncMock()
    
    # Metadata to store
    metadata = {
        "description": {"purpose": "Test project"},
        "settings": {"language": "en"}
    }
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call store_project_metadata
        await service.store_project_metadata(
            project_id="test-id",
            metadata=metadata
        )
        
        # Verify execute was called
        mock_conn.execute.assert_called_once()
        args, kwargs = mock_conn.execute.call_args
        sql = args[0]
        assert "UPDATE public.projects" in sql


@pytest.mark.asyncio
async def test_validate_schema():
    """Test schema validation."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection
    mock_conn = AsyncMock()
    
    # Setup fetchrow to return schema name
    mock_conn.fetchrow = AsyncMock(return_value={"schema_name": "test_project"})
    
    # Mock fetchval to return records count
    mock_conn.fetchval = AsyncMock(return_value=3)
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call validate_schema
        result = await service.validate_schema(project_id="test-id")
        
        # Verify the result
        assert result is True
        
        # Verify fetchval was called (we don't assert count here due to multiple calls)
        mock_conn.fetchval.assert_called()


@pytest.mark.asyncio
async def test_validate_schema_failure():
    """Test schema validation failure."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection
    mock_conn = AsyncMock()
    
    # Mock fetchval to return 0
    mock_conn.fetchval.return_value = 0
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call validate_schema
        result = await service.validate_schema(project_id="test-id")
        
        # Verify the result
        assert result is False


@pytest.mark.asyncio
async def test_get_project():
    """Test retrieving project information."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection
    mock_conn = AsyncMock()
    
    # Mock fetchrow to return a project
    mock_conn.fetchrow.return_value = {
        "id": "test-id",
        "name": "Test Project",
        "schema_name": "test_project",
        "description": '{"purpose": "Test project"}',
        "settings": '{"language": "en"}'
    }
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call get_project
        result = await service.get_project(project_id="test-id")
        
        # Verify the result
        assert result is not None
        assert result["id"] == "test-id"
        assert result["name"] == "Test Project"
        assert result["description"]["purpose"] == "Test project"
        assert result["settings"]["language"] == "en"


@pytest.mark.asyncio
async def test_get_project_not_found():
    """Test retrieving non-existent project."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection
    mock_conn = AsyncMock()
    
    # Mock fetchrow to return None
    mock_conn.fetchrow.return_value = None
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call get_project
        result = await service.get_project(project_id="nonexistent-id")
        
        # Verify the result
        assert result is None


@pytest.mark.asyncio
async def test_remove_schema():
    """Test removing a project schema."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection and transaction
    mock_conn = AsyncMock()
    mock_conn.transaction = MagicMock()
    mock_conn.transaction.return_value.__aenter__ = AsyncMock()
    mock_conn.transaction.return_value.__aexit__ = AsyncMock()
    
    # Mock execute for two calls
    mock_conn.execute = AsyncMock()
    
    # Mock fetchrow to return schema name
    mock_conn.fetchrow.return_value = {
        "schema_name": "test_project"
    }
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call remove_schema
        result = await service.remove_schema(project_id="test-id")
        
        # Verify the result
        assert result is True
        
        # Verify execute was called to drop the schema
        assert mock_conn.execute.call_count >= 1
        # In the first call it should drop the schema
        args, kwargs = mock_conn.execute.call_args_list[0]
        sql = args[0]
        assert "DROP SCHEMA" in sql or "DELETE FROM" in sql


@pytest.mark.asyncio
async def test_remove_schema_not_found():
    """Test removing a non-existent schema."""
    # Create service with mocked connection
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Mock the connection
    mock_conn = AsyncMock()
    
    # Mock fetchrow to return None
    mock_conn.fetchrow.return_value = None
    
    # Patch the _get_connection method
    with patch.object(service, '_get_connection', return_value=mock_conn):
        # Call remove_schema
        result = await service.remove_schema(project_id="nonexistent-id")
        
        # Verify the result
        assert result is False


def test_generate_schema_name():
    """Test schema name generation."""
    service = ProjectDatabaseService(connection_string="test_connection")
    
    # Test normal project name
    schema_name = service._generate_schema_name("Test Project")
    assert "test_project" in schema_name
    
    # Test project name with special characters
    schema_name = service._generate_schema_name("Test-Project.123")
    assert "test_project_123" in schema_name or "proj_test_project_123" in schema_name
    
    # Test project name with multiple spaces
    schema_name = service._generate_schema_name("  Test  Project  ")
    assert "test_project" in schema_name
    
    # Test project name with very long name (should truncate)
    long_name = "A" * 100
    schema_name = service._generate_schema_name(long_name)
    assert len(schema_name) < 100 