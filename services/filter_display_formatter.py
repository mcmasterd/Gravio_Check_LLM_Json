#!/usr/bin/env python3
"""
Filter Display Formatter
Utility để format filter_spec với icons cho dễ đọc
"""

from typing import Dict, Any

class FilterDisplayFormatter:
    """Formatter để thêm icons vào filter_spec display"""
    
    @staticmethod
    def format_filter_spec(filter_spec) -> Dict[str, Any]:
        """
        Format filter_spec với icons cho 3 phần chính:
        - user_intent_filters
        - applied_query_filters  
        - result_statistics
        
        Args:
            filter_spec: FilterSpec object
            
        Returns:
            Dict với formatted keys
        """
        if not filter_spec:
            return {}
            
        # Convert to dict nếu là object
        if hasattr(filter_spec, 'to_dict'):
            spec_dict = filter_spec.to_dict()
        else:
            spec_dict = filter_spec
            
        # Create formatted version với icons
        formatted_spec = {}
        
        # Copy tất cả fields gốc trước
        for key, value in spec_dict.items():
            if key == 'user_intent_filters':
                formatted_spec['🎯 user_intent_filters'] = value
            elif key == 'applied_query_filters':
                formatted_spec['⚙️ applied_query_filters'] = value
            elif key == 'result_statistics':
                formatted_spec['📊 result_statistics'] = value
            else:
                # Giữ nguyên các fields khác
                formatted_spec[key] = value
        
        return formatted_spec
    
    @staticmethod
    def format_filter_spec_safe(filter_spec) -> Dict[str, Any]:
        """
        Safe version - nếu có lỗi thì return original
        """
        try:
            return FilterDisplayFormatter.format_filter_spec(filter_spec)
        except Exception as e:
            # Nếu có lỗi, return original để không break system
            if hasattr(filter_spec, 'to_dict'):
                return filter_spec.to_dict()
            return filter_spec or {}
