"""
Setup script for project_management module
"""

from setuptools import setup, find_packages

setup(
    name="project_management",
    version="0.1.0",
    description="Project management module for content generator framework",
    author="ContentGenerator Team",
    author_email="team@example.com",
    packages=find_packages(),
    install_requires=[
        "asyncpg>=0.27.0",
        "psycopg2-binary>=2.9.5",
        "pydantic>=2.0.0",
        "typing-extensions>=4.5.0",
    ],
    python_requires='>=3.8',
) 