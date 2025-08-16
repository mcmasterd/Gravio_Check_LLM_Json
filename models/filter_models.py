#!/usr/bin/env python3
"""
Filter Specification Models
Extended data models cho filter processing system
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

@dataclass
class FilterSpec:
    """Unified filter specification cho toàn bộ system"""
    user_intent_filters: Dict[str, Any]      # LLM semantic filters
    api_available_filters: List[str]         # UI controls từ API
    applied_query_filters: Dict[str, Any]    # Filters thực sự used in query
    result_statistics: Dict[str, Any]        # Statistical breakdown của results
    mapping_notes: List[str]                 # Processing notes và warnings
    validation_status: str = "pending"       # pending, valid, invalid, partial
    confidence_score: float = 0.0            # Overall confidence trong mapping
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FilterSpec':
        """Create from dictionary"""
        return cls(**data)
    
    def add_mapping_note(self, note: str):
        """Add a mapping note"""
        self.mapping_notes.append(f"{datetime.now().isoformat()}: {note}")

@dataclass
class ValidationResult:
    """Result của filter validation process"""
    is_valid: bool
    supported_filters: Dict[str, Any]
    unsupported_filters: Dict[str, Any]
    suggested_alternatives: Dict[str, Any]
    confidence_score: float
    validation_notes: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

@dataclass
class FilteredProduct:
    """Enhanced product model với better typing"""
    product_id: str
    title: str
    product_type: Optional[str]
    price_min: Optional[float]
    price_max: Optional[float]
    currency: Optional[str] = "USD"
    sizes: List[str] = None
    available: Optional[bool] = None
    variants_count: int = 0
    tags: Optional[str] = None
    fit_info: Optional[str] = None
    care_info: Optional[str] = None
    description_summary: Optional[str] = None
    
    def __post_init__(self):
        if self.sizes is None:
            self.sizes = []

@dataclass
class FilteredResponse:
    """Enhanced response model với better structure"""
    status: str                              # success, empty, error, partial
    products_count: int
    products: List[FilteredProduct]
    filter_spec: Optional[FilterSpec] = None
    pagination_info: Optional[Dict[str, Any]] = None
    processing_metrics: Optional[Dict[str, Any]] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
    
    def add_error(self, error: str):
        """Add an error message"""
        self.errors.append(f"{datetime.now().isoformat()}: {error}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary với proper serialization"""
        result = asdict(self)
        # Convert products to dict if needed
        if self.products:
            result['products'] = [asdict(p) for p in self.products]
        return result

@dataclass  
class ServiceResult:
    """Generic result model cho all services"""
    success: bool
    data: Optional[Any] = None
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @classmethod
    def success_result(cls, data: Any, metadata: Dict[str, Any] = None) -> 'ServiceResult':
        """Create success result"""
        return cls(success=True, data=data, metadata=metadata or {})
    
    @classmethod
    def error_result(cls, error: str, metadata: Dict[str, Any] = None) -> 'ServiceResult':
        """Create error result"""
        return cls(success=False, error_message=error, metadata=metadata or {})
