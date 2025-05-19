"""
MODULE: modules/project_management/tests/unit/test_router.py
PURPOSE: Test the ProjectOrchestratorRouter class
CLASSES:
    - TestProjectOrchestratorRouter: Test class for router functionality
DEPENDENCIES:
    - pytest: For test framework
    - unittest.mock: For mocking dependencies
    - modules.project_management.router: For ProjectOrchestratorRouter

This module contains unit tests for the ProjectOrchestratorRouter class,
verifying that it correctly routes project creation requests to the
appropriate orchestrator based on project type.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from modules.project_management.router import ProjectOrchestratorRouter
from modules.project_management.orchestrator import ProjectOrchestrator

# Mock project response data
MOCK_PROJECT_ID = str(uuid.uuid4())
MOCK_PROJECT_RESPONSE = {
    "id": MOCK_PROJECT_ID,
    "name": "Test Project",
    "status": {
        "database": "completed",
        "vector_store": "completed",
        "templates": "completed",
        "extensions": "completed",
        "validation": "completed"
    },
    "overall_status": "success"
}

@pytest.fixture
def mock_services():
    """Create mock services for testing."""
    db_service = AsyncMock()
    vector_service = AsyncMock()
    template_service = AsyncMock()
    return db_service, vector_service, template_service

@pytest.fixture
def router(mock_services):
    """Create a ProjectOrchestratorRouter instance with mock services."""
    db_service, vector_service, template_service = mock_services
    
    # Patch the ProjectOrchestrator.__init__ to avoid actually initializing it
    with patch.object(ProjectOrchestrator, '__init__', return_value=None):
        router = ProjectOrchestratorRouter(db_service, vector_service, template_service)
        
        # Replace the actual content orchestrator with a mock
        mock_content_orchestrator = AsyncMock()
        mock_content_orchestrator.create_project.return_value = MOCK_PROJECT_RESPONSE.copy()
        mock_content_orchestrator.get_project.return_value = MOCK_PROJECT_RESPONSE.copy()
        
        router.orchestrators['content'] = mock_content_orchestrator
        
        return router

class TestProjectOrchestratorRouter:
    """Test the ProjectOrchestratorRouter class."""
    
    async def test_create_content_project(self, router):
        """Test creating a content project."""
        project_config = {
            "name": "Test Content Project",
            "type": "content",
            "description": {"purpose": "Testing"},
            "settings": {"language": "en"}
        }
        
        result = await router.create_project(project_config)
        
        # Verify the content orchestrator was called
        content_orchestrator = router.orchestrators['content']
        content_orchestrator.create_project.assert_called_once_with(project_config)
        
        # Verify the result
        assert result["id"] == MOCK_PROJECT_ID
        assert result["type"] == "content"
        assert result["overall_status"] == "success"
    
    async def test_create_project_default_type(self, router):
        """Test creating a project without specifying type defaults to 'content'."""
        project_config = {
            "name": "Test Project Without Type",
            "description": {"purpose": "Testing"},
            "settings": {"language": "en"}
        }
        
        result = await router.create_project(project_config)
        
        # Verify the content orchestrator was called
        content_orchestrator = router.orchestrators['content']
        content_orchestrator.create_project.assert_called_once()
        
        # Verify the result
        assert result["id"] == MOCK_PROJECT_ID
        assert result["type"] == "content"
    
    async def test_create_project_unsupported_type(self, router):
        """Test creating a project with an unsupported type raises ValueError."""
        project_config = {
            "name": "Test Unsupported Project",
            "type": "unsupported_type",
            "description": {"purpose": "Testing"},
            "settings": {"language": "en"}
        }
        
        with pytest.raises(ValueError) as excinfo:
            await router.create_project(project_config)
        
        assert "Unsupported project type: unsupported_type" in str(excinfo.value)
    
    async def test_get_project(self, router):
        """Test getting a project by ID."""
        result = await router.get_project(MOCK_PROJECT_ID)
        
        # Verify the content orchestrator was called
        content_orchestrator = router.orchestrators['content']
        content_orchestrator.get_project.assert_called_once_with(MOCK_PROJECT_ID)
        
        # Verify the result
        assert result["id"] == MOCK_PROJECT_ID
    
    def test_register_orchestrator(self, router):
        """Test registering a custom orchestrator."""
        # Create a mock orchestrator
        mock_orchestrator = AsyncMock()
        
        # Register it
        router.register_orchestrator("custom_type", mock_orchestrator)
        
        # Verify it was registered
        assert "custom_type" in router.orchestrators
        assert router.orchestrators["custom_type"] == mock_orchestrator
    
    def test_register_extension_to_specific_type(self, router):
        """Test registering an extension to a specific project type."""
        # Create a mock extension
        mock_extension = MagicMock()
        
        # Register it to the content orchestrator
        router.register_extension(mock_extension, "content")
        
        # Verify it was registered to the content orchestrator
        content_orchestrator = router.orchestrators["content"]
        content_orchestrator.register_extension.assert_called_once_with(mock_extension)
    
    def test_register_extension_to_all(self, router):
        """Test registering an extension to all orchestrators."""
        # Create a mock orchestrator for a custom type
        mock_orchestrator = AsyncMock()
        router.register_orchestrator("custom_type", mock_orchestrator)
        
        # Create a mock extension
        mock_extension = MagicMock()
        
        # Register it to all orchestrators
        router.register_extension(mock_extension)
        
        # Verify it was registered to both orchestrators
        content_orchestrator = router.orchestrators["content"]
        content_orchestrator.register_extension.assert_called_once_with(mock_extension)
        
        custom_orchestrator = router.orchestrators["custom_type"]
        custom_orchestrator.register_extension.assert_called_once_with(mock_extension)
    
    def test_register_extension_invalid_type(self, router):
        """Test registering an extension to an invalid project type."""
        # Create a mock extension
        mock_extension = MagicMock()
        
        # This should log a warning but not raise an exception
        router.register_extension(mock_extension, "non_existent_type")
        
        # Verify no orchestrator's register_extension was called
        content_orchestrator = router.orchestrators["content"]
        content_orchestrator.register_extension.assert_not_called() 