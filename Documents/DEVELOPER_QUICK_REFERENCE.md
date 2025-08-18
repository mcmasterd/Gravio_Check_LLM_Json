# 🚀 Shopify MCP Workflow - Developer Quick Reference

## 📋 **Quick Start Commands**

### **Basic Usage:**
```bash
# Activate environment
.\venv\Scripts\Activate.ps1

# Process all unprocessed rows
python processor.py --start-row 2 --skip-processed

# Interactive menu for beginners
python quick_start.py

# Test system health
python processor.py --test
```

### **Development Commands:**
```bash
# Install dependencies
pip install -r requirements.txt

# Run specific range
python processor.py --start-row 10 --end-row 20

# Force reprocess (ignore skip logic)
python processor.py --start-row 2 --end-row 5
```

---

## 🏗️ **File Structure Overview**

### **Core Files (CRITICAL - DO NOT DELETE):**
```
📁 Shopify_MCP/
├── processor.py                    # Main CLI entry point
├── quick_start.py                  # Interactive user interface
├── llm_keyword_extractor.py        # LLM/AI processing
├── 📁 services/
│   ├── service_container.py        # Dependency injection hub
│   ├── workflow_orchestrator.py    # Core workflow engine
│   ├── google_sheets_service.py    # Data I/O layer
│   ├── filter_mapping_service.py   # Business logic
│   ├── shopify_api_client.py       # API integration
│   ├── response_filter_service.py  # Data optimization
│   └── filter_display_formatter.py # UX enhancement
├── 📁 models/
│   ├── data_models.py             # Data structures
│   └── filter_models.py           # Filter specifications
├── 📁 config/
│   └── settings.yaml              # Configuration
└── 📁 credentials/
    └── shopify-mcp-xxx.json       # Google Sheets auth
```

---

## 🔧 **Core Classes Quick Reference**

### **WorkflowOrchestrator (Heart of System)**
```python
from services.workflow_orchestrator import WorkflowOrchestrator
from services.service_container import ServiceContainer

# Initialize
container = ServiceContainer()
orchestrator = WorkflowOrchestrator(container)

# Process data
result = orchestrator.process_sheet_data(
    start_row=2, 
    end_row=None,           # None = all rows
    skip_processed=True     # Skip rows với existing data
)

# Test health
health = orchestrator.test_all_services()
```

### **ServiceContainer (Dependency Hub)**
```python
from services.service_container import ServiceContainer

container = ServiceContainer()

# Get services
sheets = container.get_service('google_sheets')
llm = container.get_service('llm_extractor')

# Add custom service
container.add_service('my_service', my_service_instance)
```

### **LLMKeywordExtractor (AI Processing)**
```python
from llm_keyword_extractor import LLMKeywordExtractor

extractor = LLMKeywordExtractor(api_key="your-openai-key")
result = extractor.extract_keywords("blue cotton shirts")

# Result structure
result.keywords        # ["blue", "cotton", "shirts"]
result.filters         # {"colors": ["blue"], "materials": ["cotton"], "productType": "shirts"}
result.clean_query     # "blue cotton shirts"
result.confidence      # 0.95
result.reasoning       # "Extraction straightforward..."
```

---

## 📊 **Data Flow Understanding**

### **Processing Pipeline:**
```
1. Input Query (Column A) 
   ↓
2. LLM Extraction (→ Column D)
   ↓
3. Filter Mapping (semantic → API filters)
   ↓
4. API Call (Shopify MCP)
   ↓
5. Response Filtering (75% reduction)
   ↓
6. Visual Enhancement (add icons)
   ↓
7. Output (→ Column E với filter tracking)
```

### **Column Structure:**
```
A: input_text       - User query
B: query            - Processed query  
C: formatted_query  - Clean format
D: json_output      - LLM extraction result
E: api_response     - API response + filter tracking
F: filtered_response- Summary statistics
```

---

## 🎯 **Filter Tracking System**

### **Before Enhancement:**
```json
{
  "status": "success",
  "products_count": 10,
  "products": [...]
}
```

### **After Enhancement:**
```json
{
  "status": "success", 
  "products_count": 10,
  "products": [...],
  "filter_spec": {
    "🎯 user_intent_filters": {"colors": ["blue"], "productType": "shirts"},
    "⚙️ applied_query_filters": {"text_search_colors": ["blue"], "category": "shirts"},
    "📊 result_statistics": {"total_products": 10, "product_types": {"Shirts": 8, "Polos": 2}},
    "validation_status": "valid",
    "confidence_score": 1.0
  }
}
```

### **Benefits:**
- 🎯 **Track User Intent:** What user originally wanted
- ⚙️ **See Applied Filters:** What system actually used  
- 📊 **Monitor Results:** Outcome statistics
- ✅ **Debug Mismatches:** Visual identification of issues

---

## ⚡ **Performance Features**

### **Skip Processed Logic:**
```python
# Automatically skips rows với existing data
# 70-80% time savings on subsequent runs

# Manual control
python processor.py --skip-processed    # Enable (default)
python processor.py                     # Disable (force reprocess)
```

### **Batch Processing:**
```python
# Process in batches for memory efficiency
batch_size = 50  # Configurable in settings.yaml

# Progress tracking với Rich UI
# Rate limiting để avoid API limits
```

### **Data Reduction:**
```python
# ResponseFilterService reduces data by 75%
# 29KB → 6KB per response
# Faster processing, less memory usage
```

---

## 🚨 **Error Handling Patterns**

### **Service Result Pattern:**
```python
from models.filter_models import ServiceResult

# Success case
result = ServiceResult.success_result(
    data=processed_data,
    metadata={"processing_time": 1.5}
)

# Error case  
result = ServiceResult.error_result(
    error="API connection failed",
    metadata={"retry_count": 3}
)

# Check results
if result.success:
    data = result.data
else:
    error = result.error_message
```

### **Processing Result Pattern:**
```python
from models.data_models import ProcessingResult

result = ProcessingResult(
    item_id="row_5",
    row_number=5,
    json_output=llm_json,
    api_response=api_json,
    success=True,
    error_message=None,
    processing_time=2.3
)
```

---

## 🔧 **Configuration Management**

### **Main Config (config/settings.yaml):**
```yaml
google_sheets:
  credentials_file: "credentials/shopify-mcp-xxx.json"
  sheet_id: "your-sheet-id"
  sheet_name: "Detail"

shopify_api:
  base_url: "https://gravio-chat.myshopify.com/api/mcp"
  timeout: 30
  retries: 3

processing:
  batch_size: 50
  delay_between_requests: 1.0

services:
  response_filter:
    data_reduction_target: 75
    processing_timeout: 1000
```

### **Environment Variables:**
```bash
# .env file
OPENAI_API_KEY=your_openai_api_key_here

# Or PowerShell
$env:OPENAI_API_KEY="your_openai_api_key_here"
```

---

## 🧪 **Testing và Debugging**

### **Health Checks:**
```python
# Test all services
python processor.py --test

# Individual service testing
container = ServiceContainer()
sheets_service = container.get_service('google_sheets')
test_data = sheets_service.get_input_data(2, 3)
```

### **Debug Single Item:**
```python
# Process specific row for debugging
python processor.py --start-row 5 --end-row 5

# Check logs for detailed information
# Look for 🔍 [DEBUG] và ✅ [SUCCESS] messages
```

### **Common Debug Points:**
```python
# 1. LLM Extraction
llm_result = extractor.extract_keywords(query)
print(f"Confidence: {llm_result.confidence}")
print(f"Filters: {llm_result.filters}")

# 2. Filter Mapping  
filter_spec = mapper.create_filter_spec(llm_result.filters, query)
print(f"Validation: {filter_spec.validation_status}")
print(f"Applied filters: {filter_spec.applied_query_filters}")

# 3. API Response
api_result = client.search_products(query)
print(f"Success: {api_result.success}")
print(f"Product count: {len(api_result.data.get('products', []))}")
```

---

## 📈 **Performance Monitoring**

### **Key Metrics:**
```python
# Success Rate: Target >95% (Currently: 100%)
# Data Reduction: Target 75% (Currently: 78.7%)  
# Processing Time: ~1ms per response
# Memory Usage: <100MB for 1000 rows
```

### **Optimization Tips:**
```python
# 1. Use skip_processed for subsequent runs
# 2. Adjust batch_size based on memory
# 3. Increase delay_between_requests if hitting rate limits
# 4. Monitor confidence scores for LLM quality
```

---

## 🔄 **Common Workflows**

### **Daily Processing:**
```bash
# 1. Activate environment
.\venv\Scripts\Activate.ps1

# 2. Test system health
python processor.py --test

# 3. Process new data (skip existing)
python processor.py --start-row 2 --skip-processed

# 4. Check results in Google Sheets
```

### **Debugging Issues:**
```bash
# 1. Test specific range
python processor.py --start-row 10 --end-row 10

# 2. Check system health
python processor.py --test

# 3. Review error messages in console
# 4. Check configuration files
```

### **Performance Analysis:**
```bash
# 1. Run without skip to get full timing
python processor.py --start-row 2 --end-row 20

# 2. Run với skip to see improvement  
python processor.py --start-row 2 --end-row 20 --skip-processed

# 3. Compare processing times
```

---

## 🎯 **Best Practices**

### **Development:**
- ✅ Always test với `--test` before processing
- ✅ Use small ranges for debugging (`--start-row X --end-row Y`)
- ✅ Enable `--skip-processed` for production runs
- ✅ Monitor confidence scores và validation status
- ✅ Check filter_spec for debugging mismatches

### **Maintenance:**
- ✅ Regular health checks
- ✅ Monitor API quotas (OpenAI, Google Sheets)
- ✅ Archive old data periodically
- ✅ Update dependencies monthly
- ✅ Backup configuration files

### **Troubleshooting:**
- ✅ Check environment variables first
- ✅ Verify network connectivity
- ✅ Review API rate limits
- ✅ Examine error messages carefully
- ✅ Test individual components separately

---

**🔗 Quick Links:**
- [Full Architecture Guide](SYSTEM_ARCHITECTURE_GUIDE.md)
- [Configuration Reference](../config/settings.yaml)
- [Error Codes](../models/filter_models.py)
- [API Documentation](../services/shopify_api_client.py)

**📅 Last Updated:** August 18, 2025  
**🆔 Version:** 1.0
