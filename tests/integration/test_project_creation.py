"""
MODULE: modules/project_management/tests/integration/test_project_creation.py
PURPOSE: Integration tests for project creation workflow
FUNCTIONS:
    - test_end_to_end_project_creation: Tests complete project creation workflow
    - test_with_seo_extension: Tests project creation with SEO extension
    - test_recovery_from_partial_failure: Tests recovery from partial failures
DEPENDENCIES:
    - pytest: For test assertions and fixtures
    - modules.project_management: Module under test
    - services.database.db_operator: For database operations
    - services.vectorstore.vector_store_manager: For vector store operations

This module provides integration tests for the complete project creation
workflow, including extensions and error recovery scenarios.
"""

import pytest
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

from modules.project_management.orchestrator import ProjectOrchestrator
from modules.project_management.extensions.base import ProjectExtension

class TestExtension(ProjectExtension):
    """Test extension for project creation."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.executed = False
        self.validated = False
    
    async def execute(self, project_state):
        """Execute the extension."""
        self.executed = True
        
        # Add extension data to project state
        return {
            "status": "completed",
            "test_extension": {
                "executed": True,
                "config": self.config
            }
        }
    
    @property
    def requires_validation(self):
        """Extension requires validation."""
        return True
    
    async def validate(self, project_id):
        """Validate the extension execution."""
        self.validated = True
        return True

@pytest.mark.asyncio
async def test_end_to_end_project_creation():
    """Test complete project creation workflow."""
    # Set up mock services
    mock_db_service = MagicMock()
    mock_vector_service = MagicMock()
    mock_template_service = MagicMock()
    
    # Mock service methods with AsyncMock
    mock_db_service.create_schema = AsyncMock(return_value={
        "id": f"test_id_{uuid.uuid4().hex[:8]}",
        "schema_name": f"test_project_{uuid.uuid4().hex[:8]}",
        "success": True
    })
    mock_db_service.store_project_metadata = AsyncMock()
    mock_db_service.validate_schema = AsyncMock(return_value=True)
    
    mock_vector_service.create_collection = AsyncMock(return_value={
        "collection_name": f"test_collection_{uuid.uuid4().hex[:8]}",
        "success": True
    })
    mock_vector_service.store_project_vector = AsyncMock()
    mock_vector_service.validate_collection = AsyncMock(return_value=True)
    
    mock_template_service.adapt_templates = AsyncMock(return_value={
        "templates_adapted": 5,
        "success": True
    })
    mock_template_service.validate_templates = AsyncMock(return_value=True)
    
    # Create the orchestrator with mock services
    orchestrator = ProjectOrchestrator(
        db_service=mock_db_service,
        vector_service=mock_vector_service,
        template_service=mock_template_service
    )
    
    # Test project configuration
    project_config = {
        "name": "Integration Test Project",
        "description": {
            "purpose": "Testing project creation workflow",
            "audience": "Development team"
        },
        "settings": {
            "language": "en",
            "content_types": ["article", "blog_post"],
            "advanced_features": True
        }
    }
    
    # Create a project
    result = await orchestrator.create_project(project_config)
    
    # Verify result structure
    assert result is not None
    assert "id" in result
    assert "config" in result
    assert "status" in result
    assert "overall_status" in result
    
    # Verify status
    assert result["status"]["database"] == "completed"
    assert result["status"]["vector_store"] == "completed"
    assert result["status"]["templates"] == "completed"
    
    # Verify service method calls
    mock_db_service.create_schema.assert_called_once()
    mock_vector_service.create_collection.assert_called_once()
    mock_template_service.adapt_templates.assert_called_once()

@pytest.mark.asyncio
async def test_with_extension():
    """Test project creation with an extension."""
    # Set up mock services
    mock_db_service = MagicMock()
    mock_vector_service = MagicMock()
    mock_template_service = MagicMock()
    
    # Mock service methods with AsyncMock
    mock_db_service.create_schema = AsyncMock(return_value={
        "id": f"test_id_{uuid.uuid4().hex[:8]}",
        "schema_name": f"test_project_{uuid.uuid4().hex[:8]}",
        "success": True
    })
    mock_db_service.store_project_metadata = AsyncMock()
    mock_db_service.validate_schema = AsyncMock(return_value=True)
    
    mock_vector_service.create_collection = AsyncMock(return_value={
        "collection_name": f"test_collection_{uuid.uuid4().hex[:8]}",
        "success": True
    })
    mock_vector_service.store_project_vector = AsyncMock()
    mock_vector_service.validate_collection = AsyncMock(return_value=True)
    
    mock_template_service.adapt_templates = AsyncMock(return_value={
        "templates_adapted": 5,
        "success": True
    })
    mock_template_service.validate_templates = AsyncMock(return_value=True)
    
    # Create the orchestrator with mock services
    orchestrator = ProjectOrchestrator(
        db_service=mock_db_service,
        vector_service=mock_vector_service,
        template_service=mock_template_service
    )
    
    # Create a test extension with AsyncMock methods
    test_extension = TestExtension(config={"test_key": "test_value"})
    test_extension.execute = AsyncMock(return_value={
        "status": "completed",
        "test_extension": {
            "executed": True,
            "config": {"test_key": "test_value"}
        }
    })
    test_extension.validate = AsyncMock(return_value=True)
    
    # Register the extension
    orchestrator.register_extension(test_extension)
    
    # Test project configuration
    project_config = {
        "name": "Extension Test Project",
        "settings": {
            "language": "en",
            "extension_test": True
        }
    }
    
    # Create a project with the extension
    result = await orchestrator.create_project(project_config)
    
    # Verify extension was executed
    test_extension.execute.assert_called_once()
    
    # Verify extension results in project state
    assert result["status"]["extensions"] == "completed"
    assert result["overall_status"] == "partial" or result["overall_status"] == "success"

@pytest.mark.asyncio
async def test_recovery_from_partial_failure():
    """Test recovery from partial failures during project creation."""
    # Set up mock services
    mock_db_service = MagicMock()
    mock_vector_service = MagicMock()
    mock_template_service = MagicMock()
    
    # Mock database service to succeed
    mock_db_service.create_schema = AsyncMock(return_value={
        "id": f"test_id_{uuid.uuid4().hex[:8]}",
        "schema_name": f"test_project_{uuid.uuid4().hex[:8]}",
        "success": True
    })
    mock_db_service.store_project_metadata = AsyncMock()
    mock_db_service.validate_schema = AsyncMock(return_value=True)
    mock_db_service.cleanup_schema = AsyncMock(return_value=True)
    
    # Mock vector service to fail
    mock_vector_service.create_collection = AsyncMock()
    mock_vector_service.store_project_vector = AsyncMock(side_effect=Exception("Vector store error"))
    
    # Create the orchestrator with mock services
    orchestrator = ProjectOrchestrator(
        db_service=mock_db_service,
        vector_service=mock_vector_service,
        template_service=mock_template_service
    )
    
    # Test project configuration
    project_config = {
        "name": "Failure Recovery Test Project",
        "settings": {
            "language": "en"
        }
    }
    
    # Create a project
    result = await orchestrator.create_project(project_config)
    
    # Verify partial failure was detected
    assert result["status"]["database"] == "completed"
    assert result["status"]["vector_store"] == "failed"
    assert result["overall_status"] == "partial"
    assert any("Vector store error" in error for error in result["errors"])
    
    # Verify services were called appropriately
    mock_db_service.create_schema.assert_called_once()
    mock_vector_service.create_collection.assert_called_once() 