#!/usr/bin/env python3
"""
Data models for batch processing system
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re

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
    api_request: str = ""
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

# =========================
# Discovery → Targeted helpers (adapter/orchestrator)
# =========================

def _safe_get_available_filters(api_response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract available_filters array from MCP JSON-RPC response."""
    try:
        result = api_response.get("result", {}) or api_response.get("data", {})
        contents = result.get("content", [])
        for item in contents:
            if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                try:
                    as_json = json.loads(item["text"])  # text contains JSON string
                    if isinstance(as_json, dict) and "available_filters" in as_json:
                        return as_json.get("available_filters") or []
                except Exception:
                    continue
        # Fallback: direct structure
        if isinstance(result, dict) and "available_filters" in result:
            return result.get("available_filters") or []
        return []
    except Exception:
        return []


def extract_available_filters(api_response: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize available_filters into a convenient descriptor.
    Returns:
      {
        "supports": {
           "productType": bool,
           "price": bool,
           "available": bool,
           "tag": bool,
           "variantOption": {"Color": True, "Size": True, ...},
           "productMetafield": [{"namespace":"specs","key":"material"}, ...]
        },
        "raw": [...]
      }
    """
    afs = _safe_get_available_filters(api_response)
    supports: Dict[str, Any] = {
        "productType": False,
        "price": False,
        "available": False,
        "tag": False,
        "variantOption": {},
        "productMetafield": [],
    }

    for f in afs or []:
        values = (f or {}).get("values", {}) or {}
        input_opts = values.get("input_options", []) or []
        for opt in input_opts:
            inp = (opt or {}).get("input", {}) or {}
            if "productType" in inp:
                supports["productType"] = True
            if "price" in inp:
                supports["price"] = True
            if "available" in inp:
                supports["available"] = True
            if "tag" in inp:
                supports["tag"] = True
            if "variantOption" in inp:
                vo = inp.get("variantOption", {}) or {}
                name = (vo.get("name") or "").strip()
                if name:
                    supports["variantOption"][name] = True
            if "productMetafield" in inp:
                pm = inp.get("productMetafield", {}) or {}
                nk = {"namespace": pm.get("namespace"), "key": pm.get("key")}
                if nk not in supports["productMetafield"]:
                    supports["productMetafield"].append(nk)

    return {"supports": supports, "raw": afs}


def _normalize_title(s: str) -> str:
    return (s or "").strip().title()


def _normalize_upper(s: str) -> str:
    return (s or "").strip().upper()


def llm_to_mcp_filters(llm_filters: Dict[str, Any], available_filter_info: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Map LLM filters JSON into MCP filters array, keeping only supported filters."""
    out: List[Dict[str, Any]] = []
    if not isinstance(llm_filters, dict):
        return out

    supports = (available_filter_info or {}).get("supports", {}) or {}

    # productType
    if llm_filters.get("productType") and supports.get("productType"):
        out.append({"productType": _normalize_title(llm_filters["productType"])})

    # colors -> variantOption Color
    if isinstance(llm_filters.get("colors"), list) and supports.get("variantOption", {}).get("Color"):
        for c in llm_filters["colors"]:
            out.append({"variantOption": {"name": "Color", "value": _normalize_title(c)}})

    # sizes -> variantOption Size
    if isinstance(llm_filters.get("sizes"), list) and supports.get("variantOption", {}).get("Size"):
        for s in llm_filters["sizes"]:
            out.append({"variantOption": {"name": "Size", "value": _normalize_upper(s)}})

    # materials -> productMetafield if available
    if isinstance(llm_filters.get("materials"), list):
        pm_list = supports.get("productMetafield", []) or []
        material_meta = None
        for item in pm_list:
            if (item.get("key") or "").lower() == "material":
                material_meta = item
                break
        if material_meta:
            ns = material_meta.get("namespace") or "specs"
            key = material_meta.get("key") or "material"
            for m in llm_filters["materials"]:
                out.append({"productMetafield": {"namespace": ns, "key": key, "value": m}})

    # price: free-form; fill missing bound with defaults (no clamping)
    price_obj = llm_filters.get("price") or llm_filters.get("priceRange")
    if supports.get("price") and isinstance(price_obj, dict):
        DEFAULT_MIN = 0.0
        DEFAULT_MAX = 999999.0
        min_v = price_obj.get("min")
        max_v = price_obj.get("max")
        # If user supplies neither, skip
        if min_v is None and max_v is None:
            pass
        else:
            if min_v is None:
                min_v = DEFAULT_MIN
            if max_v is None:
                max_v = DEFAULT_MAX
            try:
                min_f = float(min_v)
                max_f = float(max_v)
                # If reversed, swap to form a valid range
                if min_f > max_f:
                    min_f, max_f = max_f, min_f
                out.append({"price": {"min": min_f, "max": max_f}})
            except Exception:
                pass

    # tags / sales
    if isinstance(llm_filters.get("sales"), list) and supports.get("tag"):
        for tag in llm_filters["sales"]:
            out.append({"tag": str(tag)})

    # availability
    if llm_filters.get("available") is not None and supports.get("available"):
        out.append({"available": bool(llm_filters.get("available"))})

    return out


def _pick_discovery_query(llm_json: Dict[str, Any]) -> str:
    f = (llm_json.get("filters") or {}) if isinstance(llm_json, dict) else {}
    if f.get("productType"):
        return str(f["productType"])
    kws = llm_json.get("keywords") or []
    if isinstance(kws, list) and kws:
        return str(kws[0])
    return "products"


def _pick_target_query(llm_json: Dict[str, Any]) -> str:
    return llm_json.get("clean_query") or " ".join(llm_json.get("keywords", [])) or "products"


def search_with_llm_filters(
    client: Any,
    llm_json: Dict[str, Any],
    discovery_limit: int = 5,
    targeted_limit: int = 10,
    context_prefix: str = "intelligent search",
):
    """Run Discovery -> Adapter -> Targeted using ShopifyAPIClient.
    Returns (discovery_response_json, targeted_response_json, used_filters)
    """
    # Discovery
    discovery_query = _pick_discovery_query(llm_json)
    disc_res = client.search_products(
        query=discovery_query,
        context=f"{context_prefix} - discovery search to list available filters for {discovery_query}",
        limit=discovery_limit,
    )

    if not getattr(disc_res, "success", False):
        return getattr(disc_res, "data", {}) or {}, {}, []

    disc_json = disc_res.data if isinstance(disc_res.data, dict) else disc_res.data
    af_info = extract_available_filters(disc_json)

    # Adapter
    mcp_filters = llm_to_mcp_filters((llm_json or {}).get("filters", {}), af_info)

    # Targeted
    target_query = _pick_target_query(llm_json)
    targ_res = client.search_products(
        query=target_query,
        context=f"{context_prefix} - targeted search generated from LLM filters",
        limit=targeted_limit,
        filters=mcp_filters if mcp_filters else None,
    )

    targeted_json = getattr(targ_res, "data", {}) if getattr(targ_res, "success", False) else {}
    return disc_json, targeted_json, mcp_filters
