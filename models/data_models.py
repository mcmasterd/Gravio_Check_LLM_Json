#!/usr/bin/env python3
"""
Data models for batch processing system
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json

@dataclass
class BatchItem:
    """Single item trong batch processing"""
    id: str
    input_text: str
    description: str = ""
    context: str = ""
    case: str = ""
    priority: str = "normal"
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class ProcessingResult:
    """Kết quả xử lý một item"""
    item_id: str
    row_number: int
    json_output: str = ""
    api_response: str = ""
    filtered_response: str = ""
    model_info: str = ""
    success: bool = False
    error_message: str = ""
    processing_time: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

@dataclass
class BatchJob:
    """Batch job configuration và tracking"""
    job_id: str
    input_file: str
    sheet_id: str
    sheet_name: str
    start_row: int
    total_items: int = 0
    processed_items: int = 0
    success_count: int = 0
    error_count: int = 0
    status: str = "pending"  # pending, running, completed, failed, paused
    created_at: str = ""
    updated_at: str = ""
    estimated_completion: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at

@dataclass
class ProcessingCheckpoint:
    """Checkpoint cho resume capability"""
    job_id: str
    last_processed_row: int
    last_processed_id: str
    progress_percentage: float
    processing_stats: Dict[str, Any]
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProcessingCheckpoint':
        """Create from dictionary"""
        return cls(**data)

@dataclass
class APIRequest:
    """API request structure cho JSON-RPC 2.0"""
    jsonrpc: str = "2.0"
    method: str = "tools/call"
    id: int = 1
    params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.params is None:
            self.params = {}
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)

@dataclass
class ShopifySearchParams:
    """Parameters cho search_shop_catalog"""
    name: str = "search_shop_catalog"
    arguments: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.arguments is None:
            self.arguments = {
                "query": "",
                "context": "",
                "limit": 10
            }

# Utility functions
def create_api_request_from_llm_result(llm_result: Dict[str, Any], context: str = "", limit: int = 10) -> APIRequest:
    """Tạo API request từ kết quả LLM"""
    
    # Extract query từ LLM result
    query_parts = []
    
    # Add keywords
    if "keywords" in llm_result and llm_result["keywords"]:
        query_parts.extend(llm_result["keywords"])
    
    # Add filters as query parts
    if "filters" in llm_result and llm_result["filters"]:
        for filter_type, filter_value in llm_result["filters"].items():
            if filter_type == "productType":
                query_parts.append(filter_value)
            elif filter_type == "priceRange":
                if "min" in filter_value and "max" in filter_value:
                    query_parts.append(f"price between {filter_value['min']} and {filter_value['max']}")
    
    # Create query string
    query = " ".join(query_parts) if query_parts else llm_result.get("clean_query", "")
    
    # Create search parameters
    search_params = ShopifySearchParams(
        arguments={
            "query": query,
            "context": context or f"Customer searching for: {query}",
            "limit": limit
        }
    )
    
    # Create API request
    api_request = APIRequest(
        params=asdict(search_params)
    )
    
    return api_request

def filter_api_response(response: Dict[str, Any], keep_fields: List[str] = None, 
                       remove_fields: List[str] = None, max_length: int = 5000) -> str:
    """Filter API response để chỉ giữ lại thông tin cần thiết"""
    
    if keep_fields is None:
        keep_fields = ["products", "available_filters", "pagination"]
    
    if remove_fields is None:
        remove_fields = ["debug_info", "internal_metrics", "trace_id"]
    
    # Extract result from JSON-RPC response
    if "result" in response:
        result = response["result"]
    else:
        result = response
    
    # Filter theo keep_fields
    filtered_result = {}
    for field in keep_fields:
        if field in result:
            filtered_result[field] = result[field]
    
    # Remove unwanted fields
    for field in remove_fields:
        if field in filtered_result:
            del filtered_result[field]
    
    # Convert to JSON string
    json_str = json.dumps(filtered_result, ensure_ascii=False, indent=2)
    
    # Truncate if too long
    if len(json_str) > max_length:
        json_str = json_str[:max_length] + "...[TRUNCATED]"
    
    return json_str
