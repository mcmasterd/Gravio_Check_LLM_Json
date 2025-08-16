#!/usr/bin/env python3
"""
Filter Mapping Service
Intelligent mapping giữa semantic filters và API capabilities
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from models.filter_models import FilterSpec, ValidationResult, ServiceResult
from rich.console import Console

console = Console()

class FilterMappingService:
    """Service để map semantic filters to API query parameters"""
    
    # Mapping rules từ semantic to API query construction
    SEMANTIC_TO_QUERY_MAPPING = {
        'colors': 'text_search',      # colors → add to text query
        'brands': 'text_search',      # brands → add to text query  
        'product_type': 'category',   # productType → add as category
        'productType': 'category',    # Legacy support
        'price': 'price_range',       # price → construct price query
        'materials': 'text_search',   # materials → add to text
        'sizes': 'text_search',       # sizes → add to text
        'sales': 'text_search'        # sales terms → add to text
    }
    
    # Common API available filters (will be dynamic in future)
    COMMON_API_FILTERS = ["Price", "Availability", "Product Type", "Brand"]
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize mapping service với configuration"""
        self.config = config or {}
        self.mapping_rules = self.config.get('filter_processing', {}).get('mapping_rules', {})
        self.fallback_strategy = self.config.get('filter_processing', {}).get('fallback_strategy', 'broaden_search')
        
        console.print("🔧 Filter Mapping Service initialized", style="green")
    
    def create_filter_spec(
        self, 
        semantic_filters: Dict[str, Any],
        api_available_filters: List[str] = None,
        query_context: str = ""
    ) -> FilterSpec:
        """Create comprehensive FilterSpec từ semantic filters"""
        
        if api_available_filters is None:
            api_available_filters = self.COMMON_API_FILTERS.copy()
        
        # Validate semantic filters against API capabilities
        validation = self.validate_semantic_filters(semantic_filters, api_available_filters)
        
        # Create query filters từ supported semantic filters
        applied_filters = self._create_applied_filters(validation.supported_filters)
        
        # Create filter spec
        filter_spec = FilterSpec(
            user_intent_filters=semantic_filters,
            api_available_filters=api_available_filters,
            applied_query_filters=applied_filters,
            result_statistics={},
            mapping_notes=[],
            validation_status="valid" if validation.is_valid else "partial",
            confidence_score=validation.confidence_score
        )
        
        # Add mapping notes
        for note in validation.validation_notes:
            filter_spec.add_mapping_note(note)
        
        if validation.unsupported_filters:
            filter_spec.add_mapping_note(f"Unsupported filters: {list(validation.unsupported_filters.keys())}")
        
        return filter_spec
    
    def validate_semantic_filters(
        self, 
        semantic_filters: Dict[str, Any], 
        api_available_filters: List[str]
    ) -> ValidationResult:
        """Validate semantic filters against API capabilities"""
        
        supported = {}
        unsupported = {}
        suggestions = {}
        notes = []
        
        for filter_type, filter_value in semantic_filters.items():
            if self._is_filter_supported(filter_type, api_available_filters):
                supported[filter_type] = filter_value
                notes.append(f"✅ {filter_type}: supported")
            else:
                unsupported[filter_type] = filter_value
                suggestion = self._get_filter_suggestion(filter_type, api_available_filters)
                if suggestion:
                    suggestions[filter_type] = suggestion
                    notes.append(f"⚠️ {filter_type}: unsupported, suggested: {suggestion}")
                else:
                    notes.append(f"❌ {filter_type}: unsupported, no alternative")
        
        # Calculate confidence score
        total_filters = len(semantic_filters)
        supported_count = len(supported)
        confidence = (supported_count / total_filters) if total_filters > 0 else 1.0
        
        return ValidationResult(
            is_valid=(len(unsupported) == 0),
            supported_filters=supported,
            unsupported_filters=unsupported,
            suggested_alternatives=suggestions,
            confidence_score=confidence,
            validation_notes=notes
        )
    
    def map_to_query_string(self, filter_spec: FilterSpec, base_keywords: List[str] = None) -> str:
        """Convert FilterSpec to query string cho API call"""
        
        if base_keywords is None:
            base_keywords = []
        
        query_parts = base_keywords.copy()
        
        # Process supported filters
        for filter_type, filter_value in filter_spec.applied_query_filters.items():
            query_part = self._convert_filter_to_query(filter_type, filter_value)
            if query_part:
                query_parts.append(query_part)
        
        # Fallback strategy cho unsupported filters
        if self.fallback_strategy == "broaden_search":
            unsupported_terms = self._extract_searchable_terms(
                filter_spec.user_intent_filters
            )
            query_parts.extend(unsupported_terms)
        
        final_query = " ".join(query_parts).strip()
        
        # Log mapping result
        filter_spec.add_mapping_note(f"Final query: '{final_query}'")
        
        return final_query
    
    def _is_filter_supported(self, filter_type: str, api_filters: List[str]) -> bool:
        """Check if semantic filter type is supported by API"""
        
        # Direct mapping check
        if filter_type in self.SEMANTIC_TO_QUERY_MAPPING:
            return True
        
        # Fuzzy matching với API filter names
        filter_lower = filter_type.lower()
        for api_filter in api_filters:
            if filter_lower in api_filter.lower() or api_filter.lower() in filter_lower:
                return True
        
        return False
    
    def _get_filter_suggestion(self, filter_type: str, api_filters: List[str]) -> Optional[str]:
        """Get suggestion cho unsupported filter"""
        
        suggestions_map = {
            'colors': 'Use text search with color terms',
            'materials': 'Use text search with material names',
            'styles': 'Use text search with style terms',
            'occasions': 'Use text search with occasion terms'
        }
        
        return suggestions_map.get(filter_type.lower())
    
    def _create_applied_filters(self, supported_filters: Dict[str, Any]) -> Dict[str, Any]:
        """Create applied filters từ supported semantic filters"""
        
        applied = {}
        
        for filter_type, filter_value in supported_filters.items():
            mapping_type = self.SEMANTIC_TO_QUERY_MAPPING.get(filter_type, 'text_search')
            
            if mapping_type == 'text_search':
                applied[f"text_search_{filter_type}"] = filter_value
            elif mapping_type == 'category':
                applied["category"] = filter_value
            elif mapping_type == 'price_range':
                applied["price_range"] = filter_value
            else:
                applied[filter_type] = filter_value
        
        return applied
    
    def _convert_filter_to_query(self, filter_type: str, filter_value: Any) -> Optional[str]:
        """Convert individual filter to query string"""
        
        if filter_type.startswith('text_search_'):
            if isinstance(filter_value, list):
                return " ".join(str(v) for v in filter_value)
            else:
                return str(filter_value)
        
        elif filter_type == 'category':
            return str(filter_value)
        
        elif filter_type == 'price_range':
            if isinstance(filter_value, dict):
                min_price = filter_value.get('min')
                max_price = filter_value.get('max')
                if min_price and max_price:
                    return f"price between {min_price} and {max_price}"
                elif min_price:
                    return f"price above {min_price}"
                elif max_price:
                    return f"price under {max_price}"
        
        return None
    
    def _extract_searchable_terms(self, filters: Dict[str, Any]) -> List[str]:
        """Extract searchable terms từ unsupported filters"""
        
        terms = []
        
        for filter_type, filter_value in filters.items():
            if isinstance(filter_value, list):
                terms.extend(str(v) for v in filter_value)
            elif isinstance(filter_value, str):
                terms.append(filter_value)
            elif isinstance(filter_value, dict):
                # Skip complex objects like price ranges
                continue
        
        return terms
    
    def update_result_statistics(self, filter_spec: FilterSpec, response_data: Dict[str, Any]):
        """Update FilterSpec với result statistics"""
        
        if 'products' in response_data:
            products = response_data['products']
            filter_spec.result_statistics = {
                'total_products': len(products),
                'has_results': len(products) > 0
            }
            
            # Add product type breakdown if available
            if products:
                product_types = {}
                for product in products:
                    ptype = product.get('product_type', 'Unknown')
                    product_types[ptype] = product_types.get(ptype, 0) + 1
                filter_spec.result_statistics['product_types'] = product_types
        
        filter_spec.add_mapping_note("Result statistics updated")
