# Project Management Module

## Overview
This module provides project management functionalities for the content generation framework, including project creation, schema management, and workflow orchestration.

## Components
- `orchestrator.py`: Main entry point with high-level API
- `db_operator.py`: Database operations for projects
- `services/`: Core services (database, template, vector)
- `extensions/`: Project type extensions

## Repository Setup TODO
**IMPORTANT**: This repository is currently set up as a local submodule. To properly set it up:

1. Create a GitHub repository at: https://github.com/abc-david/project_management
2. Push this code to the new repository:
   ```
   cd /home/david/python/projects/content_generator/modules/project_management
   git remote add origin https://github.com/abc-david/project_management.git
   git push -u origin master
   ```
3. Update the submodule URL in the parent project:
   ```
   cd /home/david/python/projects/content_generator
   # Edit .gitmodules to update the URL to: https://github.com/abc-david/project_management.git
   git submodule sync
   git submodule update --init --recursive
   ```

## Installation
```
pip install -e .
```

## Usage
```python
from modules.project_management.orchestrator import ProjectOrchestrator

orchestrator = ProjectOrchestrator()
project_id = await orchestrator.create_project(
    name="Example Project",
    description={"content": {"industry": "tech"}, "metadata": {"tags": ["example"]}}
)
```

## Dependencies
- asyncpg
- psycopg2-binary
- pydantic
- typing-extensions

## Key Features

- **Orchestrated Project Creation**: Coordinated creation of all project resources
- **Modular Architecture**: Clean separation of concerns between services
- **Extension System**: Optional plugins for customizing project creation
- **Transaction Safety**: Rollback on failure to prevent partial project creation
- **Comprehensive Validation**: Verification of all components after setup

## Architecture

The module follows a clean architectural pattern:

- **Core Orchestrator**: Coordinates the overall process
- **Service Modules**: Handle specific aspects of project management
- **Extension System**: Allows for optional customizations

### Directory Structure

```
/modules/project_management/
├── __init__.py                  # Main package exports
├── README.md                    # This file
├── orchestrator.py              # Central orchestration logic
├── extensions/                  # Extension system for optional features
│   ├── __init__.py
│   ├── base.py                  # Base extension class
│   └── seo_extension.py         # SEO initialization extension
└── services/                    # Specialized services
    ├── __init__.py
    ├── database_service.py      # Database operations
    ├── vector_service.py        # Vector store operations
    └── template_service.py      # Template adaptation
```

## Usage

### Basic Project Creation

```python
import asyncio
from modules.project_management import create_project

async def main():
    # Create a basic project
    project = await create_project(
        name="My Content Project",
        description={
            "purpose": "Technology blog",
            "audience": "Software developers"
        },
        settings={
            "language": "en",
            "content_types": ["blog", "tutorial", "faq"]
        }
    )
    
    print(f"Project created successfully: {project['id']}")

asyncio.run(main())
```

### Using Extensions

```python
import asyncio
from modules.project_management import create_project
from modules.project_management.extensions.seo_extension import SEOProjectExtension

async def main():
    # Create SEO extension
    seo_extension = SEOProjectExtension(
        config={
            "api_key": "your-seo-api-key"
        }
    )
    
    # Create project with SEO extension
    project = await create_project(
        name="SEO-Optimized Blog",
        description={
            "purpose": "Technology blog with SEO optimization"
        },
        settings={
            "language": "en",
            "seo_enabled": True,
            "bootstrap_seo_terrain": True,
            "seed_topics": ["artificial intelligence", "machine learning"]
        },
        extensions=[seo_extension]
    )
    
    print(f"Project created with SEO initialization: {project['id']}")

asyncio.run(main())
```

### Advanced Orchestration

```python
import asyncio
from modules.project_management import (
    ProjectOrchestrator,
    ProjectDatabaseService,
    ProjectVectorService,
    ProjectTemplateService
)

async def main():
    # Initialize services
    db_service = ProjectDatabaseService()
    vector_service = ProjectVectorService()
    template_service = ProjectTemplateService()
    
    # Create orchestrator
    orchestrator = ProjectOrchestrator(
        db_service=db_service,
        vector_service=vector_service,
        template_service=template_service
    )
    
    # Create project configuration
    project_config = {
        "name": "Custom Project",
        "description": {
            "purpose": "Custom project with advanced configuration"
        },
        "settings": {
            "language": "fr",
            "custom_setting": "value"
        }
    }
    
    # Create the project
    result = await orchestrator.create_project(project_config)
    
    print(f"Project creation status: {result['overall_status']}")
    print(f"Project ID: {result['id']}")

asyncio.run(main())
```

## Project State Management

The orchestrator maintains a project state dictionary throughout the creation process:

```python
{
    "config": {
        "name": "Project Name",
        "description": { ... },
        "settings": { ... }
    },
    "id": "uuid-string",
    "db_info": { ... },
    "status": {
        "database": "completed",
        "vector_store": "completed", 
        "templates": "completed",
        "extensions": "completed",
        "validation": "completed"
    },
    "overall_status": "success",
    "errors": []
}
```

## Adding New Extensions

To create a new extension:

1. Create a new class that extends `ProjectExtension`
2. Implement the `execute()` method
3. Optionally override `requires_validation` and `validate()` 
4. Register with the orchestrator

Example:

```python
from modules.project_management.extensions.base import ProjectExtension

class MyExtension(ProjectExtension):
    async def execute(self, project_state):
        # Implement custom logic
        return {"status": "completed", "result": "custom data"}
```

## Error Handling

The system implements robust error handling:

1. Each step has try/except blocks to catch and log errors
2. Errors are stored in the project state
3. Critical failures trigger cleanup of created resources
4. Comprehensive logging helps with debugging

## Related Documentation

- [Project Orchestration Architecture](../../docs/02_Core_Systems/project_orchestration.md)
- [Database Design](../../docs/Database%20Design.md)
- [Template Adaptation](../../services/llm/docs/template_adaptation.md)
- [Database Architecture and Schema Design](docs/database_architecture.md): Learn about the multi-schema approach, project creation workflow, and database design principles.
