#!/usr/bin/env python3
"""
Shopify API Client
Clean JSON-RPC 2.0 API client với proper error handling
"""

import requests
import json
import time
from typing import Dict, Any, Optional
from models.filter_models import ServiceResult
from rich.console import Console

console = Console()

class ShopifyAPIClient:
    """Clean API client cho Shopify MCP endpoint"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize API client với configuration"""
        api_config = config.get('api', {})
        
        self.base_url = api_config.get('base_url')
        self.timeout = api_config.get('timeout', 30)
        self.retries = api_config.get('retries', 3)
        self.headers = api_config.get('headers', {})
        
        # Setup session với persistent headers
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        console.print(f"🌐 Shopify API Client initialized for {self.base_url}", style="green")
    
    def search_products(
        self, 
        query: str, 
        context: str = "", 
        limit: int = 10
    ) -> ServiceResult:
        """Search products với clean interface"""
        
        request_body = self._create_search_request(query, context, limit)
        
        for attempt in range(self.retries):
            try:
                console.print(f"🔄 API Request (attempt {attempt + 1}/{self.retries}): {query[:50]}...", style="blue")
                
                response = self.session.post(
                    self.base_url,
                    json=request_body,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result_data = response.json()
                
                console.print("✅ API request successful", style="green")
                return ServiceResult.success_result(
                    data=result_data,
                    metadata={
                        'query': query,
                        'response_size': len(response.content),
                        'attempt': attempt + 1
                    }
                )
                
            except requests.exceptions.Timeout:
                error_msg = f"Request timeout (attempt {attempt + 1})"
                console.print(f"⏱️ {error_msg}", style="yellow")
                if attempt == self.retries - 1:
                    return ServiceResult.error_result(
                        error="Request timeout after all retries",
                        metadata={'final_attempt': attempt + 1}
                    )
                time.sleep(2 ** attempt)  # Exponential backoff
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Request failed: {str(e)}"
                console.print(f"❌ {error_msg}", style="red")
                if attempt == self.retries - 1:
                    return ServiceResult.error_result(
                        error=error_msg,
                        metadata={'final_attempt': attempt + 1}
                    )
                time.sleep(2 ** attempt)
                
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                console.print(f"💥 {error_msg}", style="red")
                return ServiceResult.error_result(
                    error=error_msg,
                    metadata={'attempt': attempt + 1}
                )
        
        return ServiceResult.error_result(
            error="All retry attempts failed",
            metadata={'total_attempts': self.retries}
        )
    
    def test_connection(self) -> ServiceResult:
        """Test API connection health"""
        
        test_query = "test connection"
        result = self.search_products(test_query, limit=1)
        
        if result.success:
            console.print("✅ API connection test successful", style="green")
            return ServiceResult.success_result(
                data={"status": "healthy", "endpoint": self.base_url},
                metadata={"test_query": test_query}
            )
        else:
            console.print("❌ API connection test failed", style="red")
            return ServiceResult.error_result(
                error=f"Connection test failed: {result.error_message}",
                metadata={"test_query": test_query}
            )
    
    def _create_search_request(self, query: str, context: str, limit: int) -> Dict[str, Any]:
        """Create JSON-RPC 2.0 request body"""
        
        return {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "id": 1,
            "params": {
                "name": "search_shop_catalog",
                "arguments": {
                    "query": query,
                    "context": context or f"Customer searching for: {query}",
                    "limit": limit
                }
            }
        }
    
    def get_request_info(self) -> Dict[str, Any]:
        """Get API client configuration info"""
        return {
            "base_url": self.base_url,
            "timeout": self.timeout,
            "retries": self.retries,
            "headers": dict(self.session.headers)
        }
