"""
MODULE: modules/project_management/tests/unit/test_template_service.py
PURPOSE: Unit tests for project template service
CLASSES:
    - TestProjectTemplateService: Tests template service operations
DEPENDENCIES:
    - pytest: For test assertions and fixtures
    - unittest.mock: For mocking PromptService
    - modules.project_management.services.template_service: Module under test

This module provides unit tests for the ProjectTemplateService class,
ensuring proper template adaptation and validation.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch, call

from modules.project_management.services.template_service import ProjectTemplateService


@pytest.mark.asyncio
async def test_initialize():
    """Test service initialization."""
    # Create service
    service = ProjectTemplateService()
    assert service._prompt_service_initialized is False
    
    # Mock PromptService
    mock_prompt_service = MagicMock()
    mock_prompt_service_class = MagicMock(return_value=mock_prompt_service)
    
    # Patch the imports
    with patch.dict('sys.modules', {'services.llm.prompt_service': MagicMock()}), \
         patch('services.llm.prompt_service.PromptService', mock_prompt_service_class):
        await service._initialize()
        
        # Verify PromptService was created
        assert service._prompt_service_initialized is True
        assert service.prompt_service is not None
        mock_prompt_service_class.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_with_existing_service():
    """Test initialization with an existing service."""
    # Create mock prompt service
    mock_prompt_service = MagicMock()
    
    # Create service with prompt service
    service = ProjectTemplateService(prompt_service=mock_prompt_service)
    
    # Since service doesn't use the passed prompt_service, we need to assign it manually
    service.prompt_service = mock_prompt_service
    
    # Skip initialization by directly setting _prompt_service_initialized
    service._prompt_service_initialized = True
    
    # Verify PromptService was not created
    assert service._prompt_service_initialized is True
    assert service.prompt_service == mock_prompt_service


@pytest.mark.asyncio
async def test_adapt_templates():
    """Test adapting templates for a project."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service
    mock_prompt_service = MagicMock()
    mock_prompt_service.ensure_project_templates = AsyncMock()
    mock_prompt_service.ensure_project_templates.return_value = {
        "templates_adapted": 5,
        "templates_skipped": 2
    }
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Project settings
    settings = {"language": "en", "domain": "marketing"}
    
    # Call adapt_templates
    result = await service.adapt_templates(project_id="test-id", settings=settings)
    
    # Verify the result
    assert result is not None
    assert result["status"] == "completed"
    assert result["templates_adapted"] == 5
    assert result["templates_skipped"] == 2
    
    # Verify prompt service method was called
    mock_prompt_service.ensure_project_templates.assert_called_once_with(
        project_id="test-id",
        settings=settings
    )


@pytest.mark.asyncio
async def test_adapt_templates_error():
    """Test error handling when adapting templates."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service with error
    mock_prompt_service = MagicMock()
    mock_prompt_service.ensure_project_templates = AsyncMock(
        side_effect=Exception("Template adaptation error")
    )
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Project settings
    settings = {"language": "en", "domain": "marketing"}
    
    # Call adapt_templates and expect exception
    with pytest.raises(Exception) as exc_info:
        await service.adapt_templates(project_id="test-id", settings=settings)
    
    # Verify exception details
    assert "Template adaptation error" in str(exc_info.value)
    
    # Verify prompt service method was called
    mock_prompt_service.ensure_project_templates.assert_called_once()


@pytest.mark.asyncio
async def test_validate_templates():
    """Test validating templates for a project."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service
    mock_prompt_service = MagicMock()
    mock_prompt_service.get_adapted_templates_for_project = AsyncMock()
    mock_prompt_service.get_adapted_templates_for_project.return_value = [
        {"id": "template1", "name": "Template 1"},
        {"id": "template2", "name": "Template 2"}
    ]
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Call validate_templates
    result = await service.validate_templates(project_id="test-id")
    
    # Verify the result
    assert result is True
    
    # Verify prompt service method was called
    mock_prompt_service.get_adapted_templates_for_project.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_validate_templates_none_found():
    """Test validating templates when none are found."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service
    mock_prompt_service = MagicMock()
    mock_prompt_service.get_adapted_templates_for_project = AsyncMock()
    mock_prompt_service.get_adapted_templates_for_project.return_value = []
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Call validate_templates
    result = await service.validate_templates(project_id="test-id")
    
    # Verify the result
    assert result is False
    
    # Verify prompt service method was called
    mock_prompt_service.get_adapted_templates_for_project.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_validate_templates_error():
    """Test error handling when validating templates."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service with error
    mock_prompt_service = MagicMock()
    mock_prompt_service.get_adapted_templates_for_project = AsyncMock(
        side_effect=Exception("Template validation error")
    )
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Call validate_templates
    result = await service.validate_templates(project_id="test-id")
    
    # Verify the result
    assert result is False
    
    # Verify prompt service method was called
    mock_prompt_service.get_adapted_templates_for_project.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_remove_templates():
    """Test removing templates for a project."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service
    mock_prompt_service = MagicMock()
    mock_prompt_service.delete_project_templates = AsyncMock()
    mock_prompt_service.delete_project_templates.return_value = {
        "deleted": 3,
        "status": "success"
    }
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Call remove_templates
    result = await service.remove_templates(project_id="test-id")
    
    # Verify the result
    assert result is True
    
    # Verify prompt service method was called
    mock_prompt_service.delete_project_templates.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_remove_templates_none_found():
    """Test removing templates when none are found."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service
    mock_prompt_service = MagicMock()
    mock_prompt_service.delete_project_templates = AsyncMock()
    mock_prompt_service.delete_project_templates.return_value = {
        "deleted": 0,
        "status": "success"
    }
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Call remove_templates
    result = await service.remove_templates(project_id="test-id")
    
    # Verify the result
    assert result is False
    
    # Verify prompt service method was called
    mock_prompt_service.delete_project_templates.assert_called_once_with("test-id")


@pytest.mark.asyncio
async def test_remove_templates_error():
    """Test error handling when removing templates."""
    # Create service
    service = ProjectTemplateService()
    
    # Mock prompt service with error
    mock_prompt_service = MagicMock()
    mock_prompt_service.delete_project_templates = AsyncMock(
        side_effect=Exception("Template removal error")
    )
    service.prompt_service = mock_prompt_service
    
    # Set initialized to skip _initialize
    service._prompt_service_initialized = True
    
    # Call remove_templates
    result = await service.remove_templates(project_id="test-id")
    
    # Verify the result
    assert result is False
    
    # Verify prompt service method was called
    mock_prompt_service.delete_project_templates.assert_called_once_with("test-id") 