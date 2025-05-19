"""
MODULE: modules/project_management/extensions/__init__.py
PURPOSE: Package for project management extensions
CLASSES: None (imports from submodules)
DEPENDENCIES: None (imports from submodules)

This package contains extension points for the project management system.
Extensions allow for customizing the project creation process with optional
functionality that's not part of the core setup.
"""

from .base import ProjectExtension

__all__ = ['ProjectExtension'] 