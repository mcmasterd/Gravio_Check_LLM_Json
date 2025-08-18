# 🔧 Shopify MCP Workflow - Troubleshooting Guide

## 🚨 **Common Issues và Solutions**

### **1. 🔑 Authentication Issues**

#### **Problem: OpenAI API Key không work**
```
❌ [ERROR] OPENAI_API_KEY not found in environment variables or .env file
```

**Solutions:**
```bash
# Option 1: Environment Variable (PowerShell)
$env:OPENAI_API_KEY="your-api-key-here"

# Option 2: .env file
echo "OPENAI_API_KEY=your-api-key-here" > .env

# Option 3: Check current setting
echo $env:OPENAI_API_KEY
```

#### **Problem: Google Sheets Access Denied**
```
❌ Failed to connect to Google Sheets: insufficient permissions
```

**Solutions:**
```bash
# 1. Check service account file exists
ls credentials/shopify-mcp-*.json

# 2. Verify file path in config
# config/settings.yaml → google_sheets.credentials_file

# 3. Check sheet sharing
# Share sheet với service account email
# Give Editor permissions
```

---

### **2. 🌐 Network và API Issues**

#### **Problem: Shopify API Connection Failed**
```
❌ API connection test failed: Connection timeout
```

**Solutions:**
```bash
# 1. Test basic connectivity
python processor.py --test

# 2. Check API endpoint
# config/settings.yaml → shopify_api.base_url

# 3. Verify network access
# Check firewall settings
# Try different network

# 4. Increase timeout
# config/settings.yaml → shopify_api.timeout: 60
```

#### **Problem: Rate Limiting**
```
⚠️ API rate limit exceeded, retrying in X seconds...
```

**Solutions:**
```yaml
# Increase delays in config/settings.yaml
processing:
  delay_between_requests: 2.0  # Increase from 1.0
  batch_size: 25              # Decrease from 50

shopify_api:
  retries: 5                  # Increase from 3
```

---

### **3. 📊 Data Processing Issues**

#### **Problem: Empty Results cho Valid Queries**
```
📊 Found 0 unprocessed items out of 17 total
```

**Diagnosis:**
```python
# Check skip logic - might be too aggressive
python processor.py --start-row 2 --end-row 5  # Force reprocess

# Check data in columns D, E, F
# If any have data, row is considered "processed"
```

**Solutions:**
```bash
# Force reprocess without skip logic
python processor.py --start-row 2 --end-row 10

# Clear specific columns if needed
# Manually delete content in Google Sheets columns D, E, F
```

#### **Problem: Low Confidence Scores**
```
🔍 [DEBUG] LLM confidence: 0.3 (below threshold)
```

**Diagnosis:**
```python
# Check query complexity
# Review LLM reasoning field
# Look for ambiguous terms
```

**Solutions:**
```python
# 1. Improve query clarity
"blue shirt" → "blue cotton dress shirt"

# 2. Check reasoning field
# Look for LLM explanation of low confidence

# 3. Review filter extraction
# Ensure filters are properly detected
```

---

### **4. 💾 Memory và Performance Issues**

#### **Problem: Out of Memory**
```
💥 Memory error during batch processing
```

**Solutions:**
```yaml
# Reduce batch size in config/settings.yaml
processing:
  batch_size: 10  # Reduce from 50

# Process smaller ranges
python processor.py --start-row 2 --end-row 20
```

#### **Problem: Slow Processing**
```
Processing taking too long...
```

**Solutions:**
```bash
# 1. Enable skip logic (if not already)
python processor.py --skip-processed

# 2. Reduce delay between requests
# config/settings.yaml → processing.delay_between_requests: 0.5

# 3. Increase batch size (if memory allows)
# config/settings.yaml → processing.batch_size: 100
```

---

### **5. 🔧 System Configuration Issues**

#### **Problem: Missing Configuration File**
```
❌ Configuration file not found: config/settings.yaml
```

**Solutions:**
```bash
# 1. Check file exists
ls config/settings.yaml

# 2. Create from template if missing
# Copy from backup or recreate

# 3. Verify YAML syntax
# Use online YAML validator
```

#### **Problem: Invalid YAML Configuration**
```
❌ Error parsing configuration: invalid YAML syntax
```

**Solutions:**
```bash
# 1. Check YAML syntax online
# Copy content to https://yaml-online-parser.appspot.com/

# 2. Common issues:
# - Missing quotes around strings
# - Incorrect indentation
# - Special characters not escaped

# 3. Restore from backup
# Use working configuration từ git history
```

---

## 🔍 **Diagnostic Commands**

### **System Health Check:**
```bash
# Full system diagnostic
python processor.py --test

# Expected output:
# ✅ Configuration loaded
# ✅ Connected to Google Sheet
# ✅ All core services initialized
# ✅ API connection test successful
```

### **Individual Component Testing:**
```python
# Test Google Sheets
from services.service_container import ServiceContainer
container = ServiceContainer()
sheets = container.get_service('google_sheets')
data = sheets.get_input_data(2, 3)
print(f"Loaded {len(data)} rows")

# Test LLM
llm = container.get_service('llm_extractor')
result = llm.extract_keywords("test query")
print(f"Confidence: {result.confidence}")

# Test API
from services.shopify_api_client import ShopifyAPIClient
client = ShopifyAPIClient(container.configuration)
health = client.test_connection()
print(f"API Health: {health.success}")
```

### **Data Validation:**
```python
# Check processed vs unprocessed rows
python -c "
from services.service_container import ServiceContainer
container = ServiceContainer()
sheets = container.get_service('google_sheets')
data = sheets.get_input_data(2, 20)

processed = 0
unprocessed = 0
for item in data:
    has_output = bool(item.get('json_output', '').strip())
    if has_output:
        processed += 1
    else:
        unprocessed += 1

print(f'Processed: {processed}, Unprocessed: {unprocessed}')
"
```

---

## 📋 **Error Code Reference**

### **ServiceResult Error Codes:**
```python
# Success
ServiceResult.success_result(data=result_data)

# Common errors
ServiceResult.error_result(error="Connection timeout")
ServiceResult.error_result(error="Invalid API key")  
ServiceResult.error_result(error="Rate limit exceeded")
ServiceResult.error_result(error="Invalid data format")
```

### **Processing Result Codes:**
```python
# Success processing
ProcessingResult(success=True, error_message=None)

# Common failures
ProcessingResult(success=False, error_message="LLM extraction failed")
ProcessingResult(success=False, error_message="API call failed") 
ProcessingResult(success=False, error_message="Response filtering failed")
ProcessingResult(success=False, error_message="Empty input text")
```

---

## 🔄 **Recovery Procedures**

### **System Recovery After Crash:**
```bash
# 1. Check what was processed
python -c "
from services.service_container import ServiceContainer
container = ServiceContainer()
sheets = container.get_service('google_sheets')
data = sheets.get_input_data(2, 100)
last_processed = max([i for i, item in enumerate(data, 2) if item.get('json_output')])
print(f'Last processed row: {last_processed}')
"

# 2. Resume from last processed + 1
python processor.py --start-row {last_processed + 1} --skip-processed
```

### **Configuration Recovery:**
```bash
# 1. Backup current config
cp config/settings.yaml config/settings.yaml.backup

# 2. Restore from working version
# Check git history hoặc manual backup

# 3. Test restored config
python processor.py --test
```

### **Data Recovery:**
```bash
# 1. Export current sheet data
# Google Sheets → File → Download → CSV

# 2. Clear problematic columns if needed
# Select columns D, E, F → Delete content

# 3. Reprocess từ clean state
python processor.py --start-row 2
```

---

## 🎯 **Performance Optimization**

### **Speed Optimization:**
```yaml
# config/settings.yaml
processing:
  batch_size: 100                    # Increase if memory allows
  delay_between_requests: 0.5        # Decrease if no rate limiting

shopify_api:
  timeout: 15                        # Decrease for faster failures
  retries: 2                         # Reduce retry attempts

services:
  response_filter:
    processing_timeout: 500          # Reduce timeout
```

### **Memory Optimization:**
```yaml
# config/settings.yaml  
processing:
  batch_size: 10                     # Reduce batch size
  
services:
  response_filter:
    data_reduction_target: 80        # Increase reduction
```

### **Reliability Optimization:**
```yaml
# config/settings.yaml
processing:
  delay_between_requests: 2.0        # Increase delays
  
shopify_api:
  timeout: 60                        # Increase timeout
  retries: 5                         # More retry attempts
```

---

## 📊 **Monitoring và Alerts**

### **Key Metrics to Monitor:**
```python
# Success Rate (target: >95%)
success_rate = successful_items / total_items

# Processing Speed (target: <2s per item)
avg_processing_time = total_time / total_items

# Error Rate (target: <5%)
error_rate = failed_items / total_items

# Confidence Score (target: >0.8)
avg_confidence = sum(confidences) / len(confidences)
```

### **Alert Conditions:**
```python
# RED ALERTS
if success_rate < 0.8:           # Success rate below 80%
if error_rate > 0.2:             # Error rate above 20%
if avg_processing_time > 10:     # Avg time > 10 seconds
if api_errors > 10:              # Too many API errors

# YELLOW ALERTS  
if success_rate < 0.95:          # Success rate below 95%
if avg_confidence < 0.7:         # Low confidence scores
if memory_usage > 500:           # High memory usage (MB)
```

---

## 🛠️ **Tools và Utilities**

### **Quick Test Script:**
```python
# test_system.py
from services.service_container import ServiceContainer

def quick_test():
    try:
        container = ServiceContainer()
        print("✅ ServiceContainer initialized")
        
        sheets = container.get_service('google_sheets')
        data = sheets.get_input_data(2, 3)
        print(f"✅ Google Sheets: {len(data)} rows loaded")
        
        llm = container.get_service('llm_extractor')
        result = llm.extract_keywords("test query")
        print(f"✅ LLM: confidence {result.confidence}")
        
        print("🎉 All systems operational!")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    quick_test()
```

### **Data Inspection Script:**
```python
# inspect_data.py
from services.service_container import ServiceContainer
import json

def inspect_data(start_row=2, end_row=10):
    container = ServiceContainer()
    sheets = container.get_service('google_sheets')
    data = sheets.get_input_data(start_row, end_row)
    
    for item in data:
        row = item.get('row_number', 'unknown')
        query = item.get('input_text', 'N/A')[:30]
        has_llm = bool(item.get('json_output', '').strip())
        has_api = bool(item.get('api_response', '').strip())
        
        status = "✅" if has_llm and has_api else "⏳" if has_llm else "❌"
        print(f"{status} Row {row}: {query}... | LLM: {has_llm} | API: {has_api}")

if __name__ == "__main__":
    inspect_data()
```

---

## 📞 **Support và Escalation**

### **Self-Service Steps:**
1. 🔍 Check this troubleshooting guide
2. 🧪 Run system health check: `python processor.py --test`
3. 📊 Inspect data với diagnostic scripts
4. 🔄 Try recovery procedures
5. 📖 Review error messages carefully

### **When to Escalate:**
- 🚨 System completely unresponsive
- 🚨 Data corruption detected
- 🚨 Security breach suspected
- 🚨 All recovery procedures failed

### **Information to Provide:**
```bash
# System information
python --version
pip list | grep -E "(openai|gspread|requests|rich)"

# Error details
# Full error messages
# Steps to reproduce
# Configuration files (remove sensitive data)
# Recent changes made
```

---

**📅 Last Updated:** August 18, 2025  
**🆔 Version:** 1.0  
**🔗 Related:** [System Architecture Guide](SYSTEM_ARCHITECTURE_GUIDE.md) | [Developer Reference](DEVELOPER_QUICK_REFERENCE.md)
