#!/usr/bin/env python3
"""
Complete System Check - Verify all components
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.service_container import ServiceContainer
from services.workflow_orchestrator import WorkflowOrchestrator
from rich.console import Console
import json

console = Console()

def check_system_completely():
    """Kiểm tra toàn bộ hệ thống"""
    
    try:
        console.print("🔍 COMPLETE SYSTEM CHECK", style="bold blue")
        console.print("=" * 60)
        
        # 1. Initialize
        console.print("\n1️⃣ Initializing system...", style="yellow")
        service_container = ServiceContainer("config/settings.yaml")
        orchestrator = WorkflowOrchestrator(service_container)
        
        # 2. Check current Google Sheets data
        console.print("\n2️⃣ Checking current Google Sheets data...", style="yellow")
        sheets_service = service_container.get_service('google_sheets')
        current_data = sheets_service.get_input_data(2, 4)
        
        console.print(f"📊 Found {len(current_data)} rows:")
        for item in current_data:
            row = item.get('row_number', 'unknown')
            input_text = item.get('input_text', 'N/A')
            json_len = len(item.get('existing_json', ''))
            api_len = len(item.get('existing_api', ''))
            
            console.print(f"  Row {row}: '{input_text}' | JSON: {json_len} chars | API: {api_len} chars")
            
            # Show preview of API response if exists
            if item.get('existing_api'):
                preview = item.get('existing_api')[:100].replace('\n', ' ')
                console.print(f"    API Preview: {preview}...")
        
        # 3. Test single item processing
        console.print("\n3️⃣ Testing single item processing...", style="yellow")
        test_item = {
            'id': 'system_check',
            'input_text': 'Arthur Ashe polo shirts',
            'description': 'System check test',
            'row_number': 999
        }
        
        result = orchestrator._process_single_item(test_item)
        
        if result.success:
            console.print("✅ Processing successful!", style="green")
            
            # Parse LLM result
            try:
                llm_data = json.loads(result.json_output)
                console.print(f"🧠 LLM: {llm_data.get('keywords', [])} | Confidence: {llm_data.get('confidence', 0):.2f}")
                console.print(f"🗺️ Filters: {llm_data.get('filters', {})}")
            except:
                console.print("⚠️ Could not parse LLM data")
            
            # Check API response
            console.print(f"🌐 API Response: {len(result.api_response)} chars")
            if "Arthur Ashe" in result.api_response:
                console.print("✅ API response contains Arthur Ashe products")
            else:
                console.print("❌ API response does NOT contain Arthur Ashe products")
            
            # Check if it's the new flow or old flow
            if "available_filters" in result.api_response and len(result.api_response) < 1000:
                console.print("❌ PROBLEM: API response is OLD FORMAT (only filters)")
            else:
                console.print("✅ API response is NEW FORMAT (full products)")
                
        else:
            console.print(f"❌ Processing failed: {result.error_message}", style="red")
        
        # 4. Check flow integration
        console.print("\n4️⃣ Checking flow integration...", style="yellow")
        
        # Check if FilterMappingService is being used
        llm_extractor = service_container.get_service('llm_extractor')
        filter_mapper = orchestrator.filter_mapper
        api_client = orchestrator.api_client
        
        console.print(f"🧠 LLM Extractor: {type(llm_extractor).__name__}")
        console.print(f"🗺️ Filter Mapper: {type(filter_mapper).__name__}")
        console.print(f"🌐 API Client: {type(api_client).__name__}")
        
        # Test LLM → FilterMapping flow
        console.print("\n5️⃣ Testing LLM → FilterMapping flow...", style="yellow")
        llm_result = llm_extractor.extract_keywords("Arthur Ashe polo shirts")
        console.print(f"LLM Result: {llm_result.keywords} | Confidence: {llm_result.confidence:.2f}")
        
        filter_spec = filter_mapper.create_filter_spec(
            semantic_filters=llm_result.filters,
            query_context="Arthur Ashe polo shirts"
        )
        
        query = filter_mapper.map_to_query_string(
            filter_spec=filter_spec,
            base_keywords=llm_result.keywords
        )
        console.print(f"Mapped Query: '{query}'")
        
        if query and "Arthur Ashe" in query:
            console.print("✅ FilterMapping working correctly")
        else:
            console.print("❌ FilterMapping NOT working correctly")
        
        console.print("\n" + "=" * 60)
        console.print("🎯 SUMMARY:", style="bold")
        
    except Exception as e:
        console.print(f"💥 System check failed: {e}", style="red")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = check_system_completely()
    if success:
        console.print("🎉 System check completed!", style="green")
    else:
        console.print("⚠️ System check failed!", style="yellow")
