"""
MODULE: modules/project_management/tests/conftest.py
PURPOSE: Provides fixtures for project management module tests
FUNCTIONS:
    - mock_database_service: Fixture that provides a mock DatabaseService
    - mock_vector_service: Fixture that provides a mock VectorService
    - mock_template_service: Fixture that provides a mock TemplateService
    - mock_orchestrator: Fixture that provides a mock ProjectOrchestrator
    - test_project_config: Fixture that provides test project configuration
DEPENDENCIES:
    - pytest: For test fixtures
    - unittest.mock: For mocking services
    - modules.project_management.orchestrator: For project orchestration

This module provides shared fixtures for project management module tests,
including mock services and test configurations.
"""

import pytest
import uuid
from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def test_project_config():
    """
    Provide a test project configuration.
    
    Returns:
        dict: A test project configuration.
    """
    return {
        "name": "Test Project",
        "description": {
            "purpose": "Testing project creation",
            "audience": "Developer team"
        },
        "settings": {
            "language": "en",
            "content_types": ["article", "blog_post", "tutorial"],
            "seo_enabled": True
        }
    }

@pytest.fixture
def mock_database_service():
    """
    Create a mock DatabaseService for testing.
    
    Returns:
        MagicMock: A mock DatabaseService.
    """
    service = MagicMock()
    
    # Mock the create_schema method
    service.create_schema = AsyncMock()
    service.create_schema.return_value = {
        "schema_name": f"test_project_{uuid.uuid4().hex[:8]}",
        "success": True
    }
    
    # Mock the validate_schema method
    service.validate_schema = AsyncMock()
    service.validate_schema.return_value = True
    
    return service

@pytest.fixture
def mock_vector_service():
    """
    Create a mock VectorService for testing.
    
    Returns:
        MagicMock: A mock VectorService.
    """
    service = MagicMock()
    
    # Mock the create_collection method
    service.create_collection = AsyncMock()
    service.create_collection.return_value = {
        "collection_name": f"test_collection_{uuid.uuid4().hex[:8]}",
        "success": True
    }
    
    # Mock the validate_collection method
    service.validate_collection = AsyncMock()
    service.validate_collection.return_value = True
    
    return service

@pytest.fixture
def mock_template_service():
    """
    Create a mock TemplateService for testing.
    
    Returns:
        MagicMock: A mock TemplateService.
    """
    service = MagicMock()
    
    # Mock the adapt_templates method
    service.adapt_templates = AsyncMock()
    service.adapt_templates.return_value = {
        "templates_adapted": 5,
        "success": True
    }
    
    # Mock the validate_templates method
    service.validate_templates = AsyncMock()
    service.validate_templates.return_value = True
    
    return service

@pytest.fixture
def mock_extension():
    """
    Create a mock ProjectExtension for testing.
    
    Returns:
        MagicMock: A mock ProjectExtension.
    """
    extension = MagicMock()
    
    # Mock the execute method
    extension.execute = AsyncMock()
    extension.execute.return_value = {
        "status": "completed",
        "extension_data": {"key": "value"}
    }
    
    # Mock the requires_validation property
    extension.requires_validation = True
    
    # Mock the validate method
    extension.validate = AsyncMock()
    extension.validate.return_value = True
    
    return extension

@pytest.fixture
def mock_orchestrator(mock_database_service, mock_vector_service, mock_template_service):
    """
    Create a mock ProjectOrchestrator for testing.
    
    Args:
        mock_database_service: Mock database service fixture.
        mock_vector_service: Mock vector service fixture.
        mock_template_service: Mock template service fixture.
        
    Returns:
        MagicMock: A mock ProjectOrchestrator.
    """
    from modules.project_management.orchestrator import ProjectOrchestrator
    
    # Create a real orchestrator with mock services
    orchestrator = ProjectOrchestrator(
        db_service=mock_database_service,
        vector_service=mock_vector_service,
        template_service=mock_template_service
    )
    
    return orchestrator 