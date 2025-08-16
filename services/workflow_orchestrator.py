#!/usr/bin/env python3
"""
Workflow Orchestrator
Clean orchestration service với dependency injection và proper error handling
"""

import time
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from models.data_models import BatchItem, ProcessingResult, BatchJob, ProcessingCheckpoint
from models.filter_models import ServiceResult, FilterSpec
from services.service_container import ServiceContainer
from services.filter_mapping_service import FilterMappingService
from services.shopify_api_client import ShopifyAPIClient
from services.response_filter_service import ResponseFilterService
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

console = Console()

class WorkflowOrchestrator:
    """Clean workflow orchestrator với dependency injection"""
    
    def __init__(self, service_container: ServiceContainer):
        """Initialize với service container"""
        self.services = service_container
        self.config = service_container.configuration
        
        # Initialize additional services
        self.filter_mapper = FilterMappingService(self.config)
        self.api_client = ShopifyAPIClient(self.config)
        self.response_filter = ResponseFilterService(self.config)
        
        # Add to service container
        service_container.add_service('filter_mapper', self.filter_mapper)
        service_container.add_service('api_client', self.api_client)
        service_container.add_service('response_filter', self.response_filter)
        
        # Processing config
        self.batch_size = self.config.get('processing', {}).get('batch_size', 50)
        self.delay_between_requests = self.config.get('processing', {}).get('delay_between_requests', 1.0)
        
        console.print("🎯 Workflow Orchestrator initialized", style="green")
    
    def process_sheet_data(
        self, 
        start_row: int = 2, 
        end_row: Optional[int] = None,
        skip_processed: bool = True
    ) -> ServiceResult:
        """Main orchestration method cho processing sheet data"""
        
        try:
            console.print("🚀 Starting workflow orchestration", style="blue")
            
            # 1. Load input data từ Google Sheets
            input_data_result = self._load_input_data(start_row, end_row)
            if not input_data_result.success:
                return input_data_result
            
            input_data = input_data_result.data
            
            # 2. Filter processed rows if requested
            if skip_processed:
                unprocessed_data = self._filter_unprocessed_rows(input_data)
                console.print(f"📊 Found {len(unprocessed_data)} unprocessed items out of {len(input_data)} total", style="blue")
            else:
                unprocessed_data = input_data
            
            if not unprocessed_data:
                console.print("✅ No items to process", style="green")
                return ServiceResult.success_result(
                    data={"processed_count": 0, "message": "No items to process"},
                    metadata={"total_items": len(input_data)}
                )
            
            # 3. Process items với progress tracking
            processing_result = self._process_batch_items(unprocessed_data)
            
            console.print("✅ Workflow orchestration completed", style="green")
            return processing_result
            
        except Exception as e:
            error_msg = f"Workflow orchestration failed: {str(e)}"
            console.print(f"❌ {error_msg}", style="red")
            return ServiceResult.error_result(error_msg)
    
    def _load_input_data(self, start_row: int, end_row: Optional[int]) -> ServiceResult:
        """Load input data từ Google Sheets"""
        
        try:
            input_data = self.services.google_sheets.get_input_data(start_row, end_row)
            
            console.print(f"📊 Loaded {len(input_data)} items from sheet", style="blue")
            return ServiceResult.success_result(
                data=input_data,
                metadata={"start_row": start_row, "end_row": end_row}
            )
            
        except Exception as e:
            error_msg = f"Failed to load input data: {str(e)}"
            console.print(f"❌ {error_msg}", style="red")
            return ServiceResult.error_result(error_msg)
    
    def _filter_unprocessed_rows(self, input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter ra unprocessed rows (rows without results in columns D, E, F)"""
        
        unprocessed = []
        
        for item in input_data:
            # Check if row đã có kết quả processing
            # Row được coi là processed nếu có ít nhất json_output (cột D) hoặc api_response (cột E)
            has_json_output = item.get('json_output', '').strip()
            has_api_response = item.get('api_response', '').strip()
            
            # Row chưa processed nếu:
            # 1. Có input_text (cột B)
            # 2. NHƯNG không có json_output (cột D) VÀ không có api_response (cột E)
            if (item.get('input_text', '').strip() and 
                not has_json_output and 
                not has_api_response):
                unprocessed.append(item)
                console.print(f"🔄 Row {item['row_number']}: '{item['input_text'][:50]}...' - unprocessed", style="dim")
            else:
                console.print(f"✅ Row {item['row_number']}: '{item['input_text'][:50]}...' - already processed", style="dim green")
        
        return unprocessed
    
    def _process_batch_items(self, items: List[Dict[str, Any]]) -> ServiceResult:
        """Process batch items với progress tracking và error handling"""
        
        total_items = len(items)
        processed_items = []
        success_count = 0
        error_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            
            task = progress.add_task(f"Processing {total_items} items...", total=total_items)
            
            for i, item in enumerate(items):
                try:
                    # Process single item
                    result = self._process_single_item(item)
                    processed_items.append(result)
                    
                    if result.success:
                        success_count += 1
                    else:
                        error_count += 1
                    
                    # Update progress
                    progress.update(task, advance=1)
                    
                    # Batch update every batch_size items
                    if (i + 1) % self.batch_size == 0 or (i + 1) == total_items:
                        self._batch_update_results(processed_items[-self.batch_size:])
                    
                    # Delay between requests
                    if i < total_items - 1:  # Not last item
                        time.sleep(self.delay_between_requests)
                        
                except Exception as e:
                    error_msg = f"Error processing item {item.get('id', 'unknown')}: {str(e)}"
                    console.print(f"⚠️ {error_msg}", style="yellow")
                    error_count += 1
                    progress.update(task, advance=1)
        
        console.print(f"✅ Processed {total_items} items: {success_count} success, {error_count} errors", style="green")
        
        return ServiceResult.success_result(
            data={
                "processed_count": total_items,
                "success_count": success_count,
                "error_count": error_count,
                "results": processed_items
            },
            metadata={
                "batch_size": self.batch_size,
                "processing_time": time.time()
            }
        )
    
    def _process_single_item(self, item: Dict[str, Any]) -> ProcessingResult:
        """Process single item through complete workflow"""
        
        start_time = time.time()
        item_id = item.get('id', str(item.get('row_number', 'unknown')))
        input_text = item.get('input_text', '')
        row_number = item.get('row_number', 0)
        
        try:
            # 1. LLM Keyword Extraction
            llm_result = self.services.llm_extractor.extract_keywords(input_text)
            llm_json = json.dumps({
                'keywords': llm_result.keywords,
                'filters': llm_result.filters,
                'clean_query': llm_result.clean_query,
                'confidence': llm_result.confidence,
                'reasoning': llm_result.reasoning
            }, ensure_ascii=False, indent=2)
            
            # 2. Create Filter Spec
            filter_spec = self.filter_mapper.create_filter_spec(
                semantic_filters=llm_result.filters,
                query_context=input_text
            )
            
            # 3. Create API Query
            query = self.filter_mapper.map_to_query_string(filter_spec, llm_result.keywords)
            
            # 4. API Call
            api_result = self.api_client.search_products(query, context=input_text)
            
            if not api_result.success:
                return ProcessingResult(
                    item_id=item_id,
                    row_number=row_number,
                    json_output=llm_json,
                    api_response=json.dumps({"error": api_result.error_message}),
                    success=False,
                    error_message=f"API call failed: {api_result.error_message}",
                    processing_time=time.time() - start_time
                )
            
            # 5. Response Filtering
            filter_result = self.response_filter.filter_response(api_result.data)
            
            if not filter_result.success:
                return ProcessingResult(
                    item_id=item_id,
                    row_number=row_number,
                    json_output=llm_json,
                    api_response=json.dumps(api_result.data, ensure_ascii=False),
                    success=False,
                    error_message=f"Response filtering failed: {filter_result.error_message}",
                    processing_time=time.time() - start_time
                )
            
            # 6. Update Filter Spec với results
            self.filter_mapper.update_result_statistics(filter_spec, filter_result.data.to_dict())
            
            # 7. Create final responses
            api_response_json = json.dumps(filter_result.data.to_dict(), ensure_ascii=False)
            summary_json = json.dumps({
                "total_products": filter_result.data.products_count,
                "status": filter_result.data.status,
                "filter_confidence": filter_spec.confidence_score,
                "processing_time_ms": filter_result.metadata.get('processing_time_ms', 0)
            }, ensure_ascii=False)
            
            console.print(f"✅ Processed item {item_id}: {filter_result.data.products_count} products found", style="green")
            
            return ProcessingResult(
                item_id=item_id,
                row_number=row_number,
                json_output=llm_json,
                api_response=api_response_json,
                filtered_response=summary_json,
                model_info=f"GPT-4o-mini (confidence: {llm_result.confidence:.2f})",
                success=True,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            error_msg = f"Processing failed for item {item_id}: {str(e)}"
            console.print(f"❌ {error_msg}", style="red")
            
            return ProcessingResult(
                item_id=item_id,
                row_number=row_number,
                success=False,
                error_message=error_msg,
                processing_time=time.time() - start_time
            )
    
    def _batch_update_results(self, results: List[ProcessingResult]):
        """Update results to Google Sheets in batch"""
        
        try:
            update_data = []
            
            for result in results:
                if result.success:
                    update_data.append({
                        'row_number': result.row_number,
                        'json_output': result.json_output,
                        'api_response': result.api_response,
                        'filtered_response': result.filtered_response,
                        'model_info': result.model_info
                    })
            
            if update_data:
                # Use existing batch update method
                for data in update_data:
                    self.services.google_sheets.update_single_row(
                        row_number=data['row_number'],
                        data={
                            'json_output': data['json_output'],
                            'api_response': data['api_response'],
                            'filtered_response': data['filtered_response'],
                            'model_info': data['model_info']
                        }
                    )
                
                console.print(f"📝 Updated {len(update_data)} rows to sheet", style="blue")
                
        except Exception as e:
            console.print(f"⚠️ Batch update failed: {str(e)}", style="yellow")
    
    def test_all_services(self) -> ServiceResult:
        """Test tất cả services connectivity"""
        
        try:
            console.print("🧪 Testing all services...", style="blue")
            
            # Test Google Sheets
            test_data = self.services.google_sheets.get_input_data(2, 3)
            console.print("✅ Google Sheets: Connected", style="green")
            
            # Test API Client
            api_test = self.api_client.test_connection()
            if api_test.success:
                console.print("✅ API Client: Connected", style="green")
            else:
                console.print(f"❌ API Client: {api_test.error_message}", style="red")
                return api_test
            
            # Test LLM Extractor
            llm_test = self.services.llm_extractor.extract_keywords("test query")
            console.print(f"✅ LLM Extractor: Working (confidence: {llm_test.confidence:.2f})", style="green")
            
            console.print("✅ All services tested successfully", style="green")
            
            return ServiceResult.success_result(
                data={"status": "all_services_healthy"},
                metadata={
                    "google_sheets": "connected",
                    "api_client": "connected", 
                    "llm_extractor": f"working (confidence: {llm_test.confidence:.2f})"
                }
            )
            
        except Exception as e:
            error_msg = f"Service testing failed: {str(e)}"
            console.print(f"❌ {error_msg}", style="red")
            return ServiceResult.error_result(error_msg)
