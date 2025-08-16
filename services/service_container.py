#!/usr/bin/env python3
"""
Service Container - Dependency Injection Pattern
Centralized service management với clean interfaces
"""

import yaml
from typing import Dict, Any, Optional
from pathlib import Path

from models.data_models import *
from models.filter_models import *
from services.google_sheets_service import GoogleSheetsService
from llm_keyword_extractor import LLMKeywordExtractor
from rich.console import Console

console = Console()

class ServiceContainer:
    """Central container cho tất cả services với dependency injection"""
    
    def __init__(self, config_file: str = "config/settings.yaml"):
        """Initialize service container với configuration"""
        self.config_file = config_file
        self.config = self._load_config()
        self._services = {}
        self._initialize_services()
        
        console.print("🏗️ Service Container initialized", style="green")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration từ YAML file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            console.print(f"✅ Configuration loaded from {self.config_file}", style="green")
            return config
        except Exception as e:
            console.print(f"❌ Failed to load config: {e}", style="red")
            raise
    
    def _initialize_services(self):
        """Initialize tất cả core services"""
        try:
            # Google Sheets Service
            self._services['google_sheets'] = GoogleSheetsService(
                credentials_file=self.config['google_sheets']['credentials_file'],
                sheet_id=self.config['google_sheets']['sheet_id'],
                sheet_name=self.config['google_sheets']['sheet_name']
            )
            
            # LLM Keyword Extractor
            self._services['llm_extractor'] = LLMKeywordExtractor()
            
            console.print("✅ All core services initialized", style="green")
            
        except Exception as e:
            console.print(f"❌ Failed to initialize services: {e}", style="red")
            raise
    
    @property
    def google_sheets(self) -> GoogleSheetsService:
        """Get Google Sheets service"""
        return self._services['google_sheets']
    
    @property
    def llm_extractor(self) -> LLMKeywordExtractor:
        """Get LLM extractor service"""
        return self._services['llm_extractor']
    
    @property
    def configuration(self) -> Dict[str, Any]:
        """Get configuration"""
        return self.config
    
    def get_service(self, service_name: str) -> Any:
        """Get service by name"""
        return self._services.get(service_name)
    
    def add_service(self, name: str, service: Any):
        """Add new service to container"""
        self._services[name] = service
        console.print(f"✅ Service '{name}' added to container", style="green")
    
    def list_services(self) -> Dict[str, str]:
        """List all available services"""
        return {name: type(service).__name__ for name, service in self._services.items()}
