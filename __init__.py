"""
Shopify MCP Workflow System

An automated batch processing system for Shopify MCP API with LLM integration.
Provides intelligent filter mapping, response optimization, and Google Sheets integration.

Version: 2.0.0 (Rebuilt)
"""

__version__ = "2.0.0"
__author__ = "Shopify MCP Team"
__description__ = "Automated workflow system for Shopify MCP API with LLM integration"

# Main components
from .processor import main as processor_main
from .quick_start import main as quick_start_main

__all__ = [
    "processor_main",
    "quick_start_main",
]
