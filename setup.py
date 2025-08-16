#!/usr/bin/env python3
"""
Setup script for Shopify MCP Workflow System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
def read_requirements(filename):
    """Read requirements from file, excluding comments and blank lines"""
    requirements = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f.readlines():
                line = line.strip()
                # Skip empty lines and comments
                if line and not line.startswith('#'):
                    # Remove inline comments
                    if '#' in line:
                        line = line.split('#')[0].strip()
                    if line:  # Check again after removing inline comments
                        requirements.append(line)
    except FileNotFoundError:
        pass  # File doesn't exist, return empty list
    return requirements

setup(
    name="shopify-mcp-workflow",
    version="2.0.0",
    description="Automated workflow system for Shopify MCP API with LLM integration",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Shopify MCP Team",
    author_email="your-email@example.com",
    url="https://github.com/your-username/shopify-mcp-workflow",
    
    packages=find_packages(),
    include_package_data=True,
    
    python_requires=">=3.8",
    install_requires=read_requirements("requirements.txt"),
    extras_require={
        "dev": read_requirements("requirements-dev.txt"),
    },
    
    entry_points={
        "console_scripts": [
            "shopify-mcp=processor:main",
            "shopify-mcp-quick=quick_start:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Office/Business :: Financial :: Point-Of-Sale",
    ],
    
    keywords="shopify mcp api llm workflow automation batch processing",
    
    project_urls={
        "Bug Reports": "https://github.com/your-username/shopify-mcp-workflow/issues",
        "Source": "https://github.com/your-username/shopify-mcp-workflow",
        "Documentation": "https://github.com/your-username/shopify-mcp-workflow#readme",
    },
)
