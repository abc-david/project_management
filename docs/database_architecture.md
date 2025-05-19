# Database Architecture and Schema Design

**Date:** 2025-05-15  
**Module:** Project Management  
**Author:** Architecture Team

## Overview

This document explains the database schema design and workflow for the Content Generator system, particularly focusing on multi-schema architecture and cross-schema operations. The system uses a carefully designed separation between project-agnostic data (stored in the public schema) and project-specific data (stored in dedicated project schemas).

## Schema Architecture

The Content Generator system uses a multi-schema PostgreSQL architecture:

### Public Schema (`public`)

The public schema stores project-agnostic data and resources that are common across all projects:

- **`public.object_models`**: Definitions of object models (e.g., TopicMap, BlogPost)
- **`public.prompts`**: Generic templates for content generation
- **`public.projects`**: Registry of all projects in the system

These tables serve as the source of truth for shared resources and enable code to function outside the context of any specific project.

### Project Schemas (`project_name`)

Each project has its own dedicated schema with project-specific tables:

- **`project_name.prompts`**: Project-adapted prompt components
- **`project_name.contents`**: Generated content for the project
- **`project_name.metadata_*`**: Project-specific metadata tables
- **`project_name.seo_*`**: Project-specific SEO tables (not covered in this document)

This isolation ensures projects don't interfere with each other and allows for project-specific customizations.

## Project Creation Workflow

When a new project is created through the `modules/project_management` module:

1. A new schema is created in the database with the project name
2. Required tables are created within the new schema:
   - `prompts` table for storing adapted prompt components
   - `contents` table for storing generated content
   - Additional metadata and SEO tables as needed

3. Project details are registered in `public.projects` table

## Template Resolution Workflow

The template resolution process integrates generic templates with project-specific adaptations:

1. `services/llm/modules/template_resolution` fetches the generic template from `public.prompts`
2. It retrieves project-adapted components from `project_name.prompts`
3. Adapted components are injected to override generic template components
4. The template undergoes resolution for:
   - Placeholder substitution
   - Context injection
   - Tool injection
   - Human message injection
   - Output format injection
   
5. `services/llm/modules/template_resolution/template_output_format_resolution.py` fetches relevant object models from `public.object_models` to define the output structure

The result is a complete, plain text prompt ready for LLM processing.

## LLM Processing

The resolved template is sent to the LLM for processing:

1. The appropriate service in `services/llm/services/langchain` sends the prompt to the LLM
2. The LLM generates structured output based on the prompt

## Output Processing

The LLM output is processed through `services/llm/modules/output_processing`:

1. Validation against Pydantic models (using `public.object_models` as the source of truth)
2. Metadata processing using project-specific metadata tables
3. Storage of the validated output:
   - In the database at `project_name.contents`
   - In the vector database within the project's ChromaDB collection

## Contents Table Design

The `contents` table in each project schema uses a dual-field approach for object model references:

```sql
CREATE TABLE "{project_name}".contents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL,
    object_model_uuid UUID REFERENCES public.object_models(id),
    object_model_name VARCHAR,
    data JSONB NOT NULL,
    metadata JSONB NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
```

### Dual-Field Reference Design

The contents table includes two complementary fields for object model references:

1. **`object_model_uuid`**: 
   - UUID reference with foreign key constraint to `public.object_models.id`
   - Enforces referential integrity
   - Ensures valid references to object models
   - Optimized for joins and indexed lookups

2. **`object_model_name`**: 
   - String field with no foreign key constraint
   - Provides human-readable context
   - Simplifies queries that don't require joins
   - Facilitates cross-schema operations where FK constraints might be challenging

This approach balances structured data integrity with flexibility required for project-specific content management.

## Advantages of This Architecture

1. **Isolation**: Each project operates in its own schema, preventing interference between projects
2. **Centralized Definitions**: Object models and templates are defined once in the public schema
3. **Customization**: Projects can customize templates while maintaining connection to the source
4. **Flexibility**: The dual-field reference approach provides both integrity and flexibility
5. **Scalability**: New projects can be added without modifying existing database structures
6. **Maintainability**: Clear separation between project-agnostic and project-specific data

## Implementation Guidelines

When implementing features that interact with this architecture:

1. Use `public` schema for project-agnostic resources only
2. Store all project-specific data in the project's schema
3. Always populate both `object_model_uuid` and `object_model_name` when creating content records
4. Use UUID references for joins and data integrity checks
5. Use name references for display and human-readable contexts
6. Follow the template resolution workflow for consistent LLM prompting

## Conclusion

This multi-schema architecture with dual-field references provides a robust foundation for the Content Generator system. It balances data integrity with operational flexibility, allowing each project to have customized content while maintaining connections to centralized object models and templates. 