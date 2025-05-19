# Project Management Module Testing

## Overview

This directory contains tests for the Project Management module, which is responsible for coordinating various services to create, manage, and maintain projects within the Content Generator system.

## Test Structure

The tests are organized into different directories:

- **Unit Tests** (`unit/`): Tests for individual components in isolation
- **Integration Tests** (`integration/`): Tests for interactions between multiple components
- **Fixtures** (`conftest.py`): Shared test fixtures and mocks

## Test Types

### Unit Tests

Unit tests validate the functionality of individual components within the Project Management module. These tests use mock objects to isolate the component under test from its dependencies.

Current unit tests:
- `test_orchestrator.py`: Tests for the `ProjectOrchestrator` class
- `test_database_service.py`: Tests for the `ProjectDatabaseService` class
- `test_vector_service.py`: Tests for the `ProjectVectorService` class
- `test_template_service.py`: Tests for the `ProjectTemplateService` class

### Integration Tests

Integration tests validate the interactions between multiple components, ensuring they work together as expected. These tests focus on complete workflows and processes.

Current integration tests:
- `test_project_creation.py`: Tests for the project creation workflow
- `test_project_workflow.py`: Tests for the full project lifecycle

## Running Tests

### Running Tests with `pytest`

You can run all tests using `pytest`:

```bash
# Run all tests
pytest modules/project_management/tests/

# Run unit tests only
pytest modules/project_management/tests/unit/

# Run integration tests only
pytest modules/project_management/tests/integration/

# Run a specific test file
pytest modules/project_management/tests/unit/test_orchestrator.py
```

### Running Tests with Verbose Output

For more detailed output, use the `-v` flag:

```bash
pytest -v modules/project_management/tests/
```

### Running Async Tests

The tests use `pytest-asyncio` for testing async functions. The `@pytest.mark.asyncio` decorator is used to mark tests that contain async functions.

## Test Fixtures

The `conftest.py` file contains fixtures that are shared across tests. These include:

- `test_project_config`: Provides a sample project configuration for testing
- `mock_database_service`: Provides a mock implementation of `ProjectDatabaseService`
- `mock_vector_service`: Provides a mock implementation of `ProjectVectorService`
- `mock_template_service`: Provides a mock implementation of `ProjectTemplateService`
- `mock_extension`: Provides a mock implementation of `ProjectExtension`
- `mock_orchestrator`: Provides a `ProjectOrchestrator` instance with mock services

## Mocking Strategy

The tests use a comprehensive mocking strategy to isolate components:

1. **Service Mocking**: External services are mocked to prevent actual database, vector store, or template operations during testing.
   
2. **Method Mocking**: Methods that perform external operations or depend on external services are mocked to ensure tests run in isolation.
   
3. **Extension Mocking**: Project extensions are mocked to verify they are properly executed during the project lifecycle.

## Test Data

Test data is generated using a combination of:

- Static test data defined in fixtures
- Dynamically generated UUIDs and identifiers
- Mock response objects that simulate service responses

## Adding New Tests

When adding new tests, follow these guidelines:

1. **Unit Tests**:
   - Place unit tests in the `unit/` directory
   - Name the test file `test_<component_name>.py`
   - Mock all external dependencies
   - Test each method in isolation

2. **Integration Tests**:
   - Place integration tests in the `integration/` directory
   - Name the test file `test_<workflow_name>.py`
   - Test complete workflows and processes
   - Use fixtures from `conftest.py` where possible

3. **Test Coverage**:
   - Ensure tests cover normal operation
   - Include tests for error conditions and edge cases
   - Test validation and cleanup operations

## Error Handling and Recovery Testing

A key aspect of the Project Management module is its ability to handle errors and recover from failures. The tests include specific scenarios to validate this functionality:

- Partial failures during project creation
- Validation failures
- Cleanup after failures
- Error propagation

## State Consistency Testing

The tests verify that project state is consistently maintained throughout the workflow:

- State transitions during different phases
- State persistence across component boundaries
- State recovery after errors

## Extension Testing

The Project Management module supports extensions that can be registered to extend its functionality. The tests include validation of:

- Extension registration
- Extension execution during the project lifecycle
- Extension validation
- Extension error handling 