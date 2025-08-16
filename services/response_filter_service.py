#!/usr/bin/env python3
"""
Response Filter Service
Simplified và optimized response filtering với clear architecture
"""

import json
import re
import time
from typing import Dict, List, Any, Optional, Tuple
from models.filter_models import FilteredProduct, FilteredResponse, ServiceResult
from rich.console import Console

console = Console()

class ResponseFilterService:
    """Simplified service để filter và optimize API responses"""
    
    # Size ordering constants
    SIZE_ORDER = ["XXXS", "XXS", "XS", "S", "M", "L", "XL", "XXL", "XXXL", "XXXXL"]
    
    # Common extraction patterns
    FIT_PATTERNS = [
        (re.compile(r"oversized", re.I), "Oversized"),
        (re.compile(r"true[- ]?to[- ]?size", re.I), "True-to-size"),
        (re.compile(r"regular fit", re.I), "Regular"),
        (re.compile(r"slim fit", re.I), "Slim"),
        (re.compile(r"relaxed fit", re.I), "Relaxed")
    ]
    
    CARE_PATTERNS = [
        (re.compile(r"dry\s*clean\s*only", re.I), "Dry clean only"),
        (re.compile(r"machine\s*w(ash|ashing)\s*cold", re.I), "Machine wash cold"),
        (re.compile(r"do not tumble dry", re.I), "Do not tumble dry")
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize response filter service"""
        self.config = config or {}
        self.target_reduction = self.config.get('services', {}).get('response_filter', {}).get('data_reduction_target', 75)
        self.processing_timeout = self.config.get('services', {}).get('response_filter', {}).get('processing_timeout', 1000)
        
        console.print("🔧 Response Filter Service initialized", style="green")
    
    def filter_response(self, raw_response: Dict[str, Any]) -> ServiceResult:
        """Main method để filter API response với performance tracking"""
        
        start_time = time.time()
        
        try:
            # Extract products từ response
            products_data = self._extract_products_data(raw_response)
            
            # Filter individual products
            filtered_products = []
            for product_data in products_data:
                filtered_product = self._filter_single_product(product_data)
                if filtered_product:
                    filtered_products.append(filtered_product)
            
            # Extract metadata
            pagination_info = self._extract_pagination_info(raw_response)
            available_filters = self._extract_available_filters(raw_response)
            
            # Calculate processing metrics
            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            
            # Create filtered response
            filtered_response = FilteredResponse(
                status="success" if filtered_products else "empty",
                products_count=len(filtered_products),
                products=filtered_products,
                pagination_info=pagination_info,
                processing_metrics={
                    "processing_time_ms": round(processing_time, 2),
                    "products_processed": len(products_data),
                    "products_filtered": len(filtered_products),
                    "target_reduction": self.target_reduction
                }
            )
            
            # Calculate data reduction
            original_size = len(json.dumps(raw_response))
            filtered_size = len(json.dumps(filtered_response.to_dict()))
            reduction_percent = ((original_size - filtered_size) / original_size) * 100
            
            console.print(f"🔧 Response filtered: {original_size} → {filtered_size} chars ({reduction_percent:.1f}% reduction)", style="cyan")
            console.print(f"⚡ Processing time: {processing_time:.1f}ms", style="blue")
            
            return ServiceResult.success_result(
                data=filtered_response,
                metadata={
                    "original_size": original_size,
                    "filtered_size": filtered_size,
                    "reduction_percent": reduction_percent,
                    "processing_time_ms": processing_time
                }
            )
            
        except Exception as e:
            error_msg = f"Response filtering failed: {str(e)}"
            console.print(f"❌ {error_msg}", style="red")
            return ServiceResult.error_result(
                error=error_msg,
                metadata={"processing_time_ms": (time.time() - start_time) * 1000}
            )
    
    def _extract_products_data(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract products array từ response structure"""
        
        # Direct products array
        if isinstance(response.get("products"), list):
            return response["products"]
        
        # Nested trong result.content[].text (JSON-RPC 2.0)
        try:
            content = response.get("result", {}).get("content", [])
            if isinstance(content, list) and content:
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text":
                        text_content = item.get("text", "")
                        if text_content.strip().startswith("{"):
                            inner_data = json.loads(text_content)
                            if isinstance(inner_data.get("products"), list):
                                return inner_data["products"]
        except (json.JSONDecodeError, KeyError):
            pass
        
        return []
    
    def _filter_single_product(self, product_data: Dict[str, Any]) -> Optional[FilteredProduct]:
        """Filter single product với optimized extraction"""
        
        try:
            # Basic info
            product_id = product_data.get("product_id") or product_data.get("id", "")
            title = product_data.get("title", "")
            product_type = product_data.get("product_type")
            
            # Price extraction
            price_min, price_max, currency = self._extract_price_info(product_data)
            
            # Variants processing
            variants = product_data.get("variants", [])
            sizes = self._extract_sizes(variants)
            available = self._determine_availability(variants)
            
            # Text processing
            tags = self._process_tags(product_data.get("tags"))
            fit_info = self._extract_fit_info(product_data)
            care_info = self._extract_care_info(product_data)
            description = self._extract_description(product_data)
            
            return FilteredProduct(
                product_id=product_id,
                title=title,
                product_type=product_type,
                price_min=price_min,
                price_max=price_max,
                currency=currency,
                sizes=sizes,
                available=available,
                variants_count=len(variants),
                tags=tags,
                fit_info=fit_info,
                care_info=care_info,
                description_summary=description
            )
            
        except Exception as e:
            console.print(f"⚠️ Error filtering product {product_data.get('product_id', 'unknown')}: {e}", style="yellow")
            return None
    
    def _extract_price_info(self, product_data: Dict[str, Any]) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """Extract price information"""
        price_min = product_data.get("price_min")
        price_max = product_data.get("price_max")
        currency = product_data.get("currency", "USD")
        
        return price_min, price_max, currency
    
    def _extract_sizes(self, variants: List[Dict[str, Any]]) -> List[str]:
        """Extract và sort sizes từ variants"""
        sizes = set()
        
        for variant in variants:
            if isinstance(variant, dict):
                # Check various size fields
                size_value = (variant.get("size") or 
                            variant.get("option1") or 
                            variant.get("title", ""))
                
                if size_value and isinstance(size_value, str):
                    size_clean = size_value.strip().upper()
                    if size_clean in self.SIZE_ORDER:
                        sizes.add(size_clean)
        
        # Sort sizes according to SIZE_ORDER
        sorted_sizes = [size for size in self.SIZE_ORDER if size in sizes]
        return sorted_sizes
    
    def _determine_availability(self, variants: List[Dict[str, Any]]) -> Optional[bool]:
        """Determine product availability từ variants"""
        if not variants:
            return None
        
        available_count = sum(1 for v in variants if v.get("available", False))
        return available_count > 0
    
    def _process_tags(self, tags_data: Any) -> Optional[str]:
        """Process và clean tags"""
        if not tags_data:
            return None
        
        if isinstance(tags_data, list):
            return ", ".join(str(tag) for tag in tags_data[:5])  # Limit to 5 tags
        elif isinstance(tags_data, str):
            return tags_data[:100]  # Limit length
        
        return None
    
    def _extract_fit_info(self, product_data: Dict[str, Any]) -> Optional[str]:
        """Extract fit information from product data"""
        text_fields = [
            product_data.get("description", ""),
            product_data.get("body_html", ""),
            product_data.get("title", "")
        ]
        
        full_text = " ".join(str(field) for field in text_fields if field)
        
        for pattern, fit_type in self.FIT_PATTERNS:
            if pattern.search(full_text):
                return fit_type
        
        return None
    
    def _extract_care_info(self, product_data: Dict[str, Any]) -> Optional[str]:
        """Extract care instructions"""
        text_fields = [
            product_data.get("description", ""),
            product_data.get("body_html", ""),
            product_data.get("care_instructions", "")
        ]
        
        full_text = " ".join(str(field) for field in text_fields if field)
        
        care_instructions = []
        for pattern, care_type in self.CARE_PATTERNS:
            if pattern.search(full_text):
                care_instructions.append(care_type)
        
        return ", ".join(care_instructions) if care_instructions else None
    
    def _extract_description(self, product_data: Dict[str, Any]) -> Optional[str]:
        """Extract summary description"""
        description = product_data.get("description") or product_data.get("body_html", "")
        
        if description and isinstance(description, str):
            # Clean HTML tags and limit length
            clean_desc = re.sub(r'<[^>]+>', '', description)
            return clean_desc[:200] + "..." if len(clean_desc) > 200 else clean_desc
        
        return None
    
    def _extract_pagination_info(self, response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract pagination information"""
        return response.get("pagination_info") or response.get("pagination")
    
    def _extract_available_filters(self, response: Dict[str, Any]) -> Optional[List[str]]:
        """Extract available filters từ response"""
        return response.get("available_filters")
