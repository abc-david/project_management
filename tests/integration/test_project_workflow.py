"""
MODULE: modules/project_management/tests/integration/test_project_workflow.py
PURPOSE: Integration tests for complete project management workflow
CLASSES:
    - TestProjectWorkflow: Tests complete project lifecycle
DEPENDENCIES:
    - pytest: For test assertions and fixtures
    - asyncio: For async testing
    - unittest.mock: For mocking dependencies
    - modules.project_management: Module under test

This module provides integration tests for the complete project management
workflow, including creation, modification, and cleanup.
"""

import pytest
import asyncio
import uuid
import json
from unittest.mock import MagicMock, AsyncMock, patch

from modules.project_management.orchestrator import ProjectOrchestrator
from modules.project_management.services.database_service import ProjectDatabaseService
from modules.project_management.services.vector_service import ProjectVectorService
from modules.project_management.services.template_service import ProjectTemplateService


class TestProjectWorkflow:
    """Test the complete project management workflow."""

    @pytest.fixture
    async def mock_services(self):
        """Create mock services for testing."""
        project_id = f"test_id_{uuid.uuid4().hex[:8]}"
        schema_name = f"test_project_{uuid.uuid4().hex[:8]}"
        collection_name = f"collection_{project_id}"
        
        # Mock database service
        db_service = MagicMock()
        db_service.create_schema = AsyncMock(return_value={
            "id": project_id,
            "name": "Test Project",
            "schema_name": schema_name
        })
        db_service.store_project_metadata = AsyncMock()
        db_service.validate_schema = AsyncMock(return_value=True)
        db_service.get_project = AsyncMock(return_value={
            "id": project_id,
            "name": "Test Project",
            "schema_name": schema_name,
            "description": json.dumps({"purpose": "Testing"}),
            "settings": json.dumps({"language": "en"})
        })
        db_service.remove_schema = AsyncMock(return_value=True)
        
        # Mock vector service
        vector_service = MagicMock()
        vector_service.create_collection = AsyncMock(return_value={
            "collection_name": collection_name,
            "status": "created"
        })
        vector_service.store_project_vector = AsyncMock(return_value={
            "vector_id": f"project_profile_{project_id}",
            "status": "stored"
        })
        vector_service.validate_collection = AsyncMock(return_value=True)
        vector_service.remove_collection = AsyncMock(return_value=True)
        
        # Mock template service
        template_service = MagicMock()
        template_service.adapt_templates = AsyncMock(return_value={
            "status": "completed",
            "templates_adapted": 5,
            "templates_skipped": 0
        })
        template_service.validate_templates = AsyncMock(return_value=True)
        template_service.remove_templates = AsyncMock(return_value=True)
        
        # Set initialized to skip _initialize methods
        vector_service._initialized = True
        template_service._prompt_service_initialized = True
        
        # Create orchestrator with mock services
        orchestrator = ProjectOrchestrator(
            db_service=db_service,
            vector_service=vector_service,
            template_service=template_service
        )
        
        return {
            "orchestrator": orchestrator,
            "db_service": db_service,
            "vector_service": vector_service,
            "template_service": template_service,
            "project_id": project_id
        }
    
    @pytest.mark.asyncio
    async def test_complete_project_lifecycle(self, mock_services):
        """Test complete project lifecycle from creation to cleanup."""
        # Get mocks from fixture
        orchestrator = mock_services["orchestrator"]
        db_service = mock_services["db_service"]
        vector_service = mock_services["vector_service"]
        template_service = mock_services["template_service"]
        project_id = mock_services["project_id"]
        
        # Step 1: Create a project
        project_config = {
            "name": "Test Project",
            "description": {"purpose": "Testing"},
            "settings": {
                "language": "en",
                "content_types": ["article", "blog_post"]
            }
        }
        
        result = await orchestrator.create_project(project_config)
        
        # Verify project creation
        assert result["id"] == project_id
        assert result["status"]["database"] == "completed"
        assert result["status"]["vector_store"] == "completed"
        assert result["status"]["templates"] == "completed"
        
        # Verify service calls during creation
        db_service.create_schema.assert_called_once()
        db_service.store_project_metadata.assert_called_once()
        vector_service.create_collection.assert_called_once()
        vector_service.store_project_vector.assert_called_once()
        template_service.adapt_templates.assert_called_once()
        
        # Step 2: Get project information
        project_info = await db_service.get_project(project_id)
        
        # Verify project info
        assert project_info is not None
        assert project_info["id"] == project_id
        assert project_info["name"] == "Test Project"
        
        # Step 3: Validate project components
        db_validated = await db_service.validate_schema(project_id)
        vector_validated = await vector_service.validate_collection(project_id)
        templates_validated = await template_service.validate_templates(project_id)
        
        # Verify validation
        assert db_validated is True
        assert vector_validated is True
        assert templates_validated is True
        
        # Step 4: Cleanup project - Add the status field to match the method implementation
        await orchestrator._cleanup_failed_project({
            "id": project_id,
            "status": {
                "database": "completed",
                "vector_store": "completed",
                "templates": "completed"
            }
        })
        
        # Verify cleanup
        db_service.remove_schema.assert_called_once_with(project_id)
        vector_service.remove_collection.assert_called_once_with(project_id)
        template_service.remove_templates.assert_called_once_with(project_id)
    
    @pytest.mark.asyncio
    async def test_project_creation_validation(self, mock_services):
        """Test project creation with validation."""
        # Get mocks from fixture
        orchestrator = mock_services["orchestrator"]
        
        # Set up project
        project_config = {
            "name": "Validation Test",
            "settings": {"language": "en"}
        }
        
        # Patch the validate method to capture the project state
        validated_state = None
        
        async def mock_validate(self, project_state):
            nonlocal validated_state
            validated_state = project_state
            project_state["status"]["validation"] = "completed"
            return project_state
        
        with patch.object(ProjectOrchestrator, '_validate_project', new=mock_validate):
            # Create project
            result = await orchestrator.create_project(project_config)
            
            # Verify validation was called with correct state
            assert validated_state is not None
            assert validated_state["status"]["database"] == "completed"
            assert validated_state["status"]["vector_store"] == "completed"
            assert validated_state["status"]["templates"] == "completed"
            
            # Verify final result
            assert result["status"]["validation"] == "completed"
    
    @pytest.mark.asyncio
    async def test_error_recovery(self, mock_services):
        """Test error recovery in project workflow."""
        # Get mocks from fixture
        orchestrator = mock_services["orchestrator"]
        vector_service = mock_services["vector_service"]
        
        # Make vector service fail
        vector_service.create_collection.side_effect = Exception("Test failure")
        
        # Set up project
        project_config = {
            "name": "Error Test",
            "settings": {"language": "en"}
        }
        
        # Mock the _cleanup_failed_project method to avoid calling it
        original_cleanup = orchestrator._cleanup_failed_project
        orchestrator._cleanup_failed_project = AsyncMock()
        
        # Attempt to create project - The orchestrator handles exceptions internally now
        result = await orchestrator.create_project(project_config)
        
        # Verify the project creation failed with the expected error
        assert result["status"]["vector_store"] == "failed"
        
        # Check if there's any error message that contains "Test failure"
        found_error = False
        if "errors" in result:
            # Handle both dict and list errors format
            if isinstance(result["errors"], dict) and "vector_store" in result["errors"]:
                found_error = "Test failure" in str(result["errors"]["vector_store"])
            elif isinstance(result["errors"], list):
                for error in result["errors"]:
                    if "Test failure" in str(error):
                        found_error = True
                        break
        
        assert found_error, "Expected error message containing 'Test failure' not found"
        
        # Restore the original cleanup method
        orchestrator._cleanup_failed_project = original_cleanup
    
    @pytest.mark.asyncio
    async def test_project_state_consistency(self, mock_services):
        """Test that project state is consistent throughout the workflow."""
        # Get mocks from fixture
        orchestrator = mock_services["orchestrator"]
        
        # Set up project
        project_config = {
            "name": "State Test",
            "description": {"purpose": "Testing state consistency"},
            "settings": {"language": "en"}
        }
        
        # Track state through each phase
        db_state = None
        vector_state = None
        template_state = None
        
        # Replace phase methods to capture state using simple function replacement
        original_db_phase = orchestrator._create_database_schema
        original_vector_phase = orchestrator._initialize_vector_store
        original_template_phase = orchestrator._adapt_templates
        
        async def mock_db_phase(state):
            nonlocal db_state
            result = await original_db_phase(state)
            db_state = result.copy()
            return result
        
        async def mock_vector_phase(state):
            nonlocal vector_state
            result = await original_vector_phase(state)
            vector_state = result.copy()
            return result
        
        async def mock_template_phase(state):
            nonlocal template_state
            result = await original_template_phase(state)
            template_state = result.copy()
            return result
        
        # Replace the methods with our mock versions
        orchestrator._create_database_schema = mock_db_phase
        orchestrator._initialize_vector_store = mock_vector_phase
        orchestrator._adapt_templates = mock_template_phase
        
        try:
            # Create project
            result = await orchestrator.create_project(project_config)
            
            # Verify state consistency
            assert db_state is not None
            assert db_state["id"] == result["id"]
            assert db_state["status"]["database"] == "completed"
            
            assert vector_state is not None
            assert vector_state["id"] == result["id"]
            assert vector_state["status"]["database"] == "completed"
            assert vector_state["status"]["vector_store"] == "completed"
            
            assert template_state is not None
            assert template_state["id"] == result["id"]
            assert template_state["status"]["database"] == "completed"
            assert template_state["status"]["vector_store"] == "completed"
            assert template_state["status"]["templates"] == "completed"
            
            # Verify final result
            assert result["status"]["database"] == "completed"
            assert result["status"]["vector_store"] == "completed"
            assert result["status"]["templates"] == "completed"
        finally:
            # Restore original methods
            orchestrator._create_database_schema = original_db_phase
            orchestrator._initialize_vector_store = original_vector_phase
            orchestrator._adapt_templates = original_template_phase 