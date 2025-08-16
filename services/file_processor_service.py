#!/usr/bin/env python3
"""
File Processor service để xử lý input files
"""

import csv
import json
from typing import List, Dict, Any, Generator
from pathlib import Path
from rich.console import Console

console = Console()

class FileProcessorService:
    """Service để xử lý nhiều loại input files"""
    
    def __init__(self):
        self.supported_formats = ['.csv', '.json', '.jsonl', '.txt']
        console.print("✅ File Processor Service initialized", style="green")
    
    def detect_file_format(self, file_path: str) -> str:
        """Auto detect file format"""
        suffix = Path(file_path).suffix.lower()
        if suffix not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {suffix}")
        return suffix
    
    def load_data(self, file_path: str) -> List[Dict[str, Any]]:
        """Load data từ file"""
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        format_type = self.detect_file_format(file_path)
        
        console.print(f"📂 Loading data from {file_path} (format: {format_type})", style="blue")
        
        if format_type == '.csv':
            return self._load_csv(file_path)
        elif format_type == '.json':
            return self._load_json(file_path)
        elif format_type == '.jsonl':
            return self._load_jsonlines(file_path)
        elif format_type == '.txt':
            return self._load_text(file_path)
        else:
            raise ValueError(f"Unsupported format: {format_type}")
    
    def _load_csv(self, file_path: str) -> List[Dict[str, Any]]:
        """Load CSV file"""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            # Auto detect delimiter
            sample = f.read(1024)
            f.seek(0)
            sniffer = csv.Sniffer()
            delimiter = sniffer.sniff(sample).delimiter
            
            reader = csv.DictReader(f, delimiter=delimiter)
            
            for row_num, row in enumerate(reader, start=1):
                # Clean và validate data
                cleaned_row = {}
                
                # Map các columns
                cleaned_row['id'] = row.get('id', str(row_num))
                cleaned_row['input_text'] = row.get('input_text', '').strip()
                cleaned_row['description'] = row.get('description', '').strip()
                cleaned_row['context'] = row.get('context', '').strip()
                cleaned_row['case'] = row.get('case', '').strip()
                cleaned_row['priority'] = row.get('priority', 'normal').strip()
                
                # Generate ID if not provided
                if not cleaned_row['id']:
                    cleaned_row['id'] = str(row_num)
                
                # Skip empty rows
                if not cleaned_row['input_text']:
                    continue
                
                # Add metadata
                cleaned_row['row_number'] = row_num + 1  # +1 for header
                cleaned_row['original_data'] = dict(row)
                
                data.append(cleaned_row)
        
        console.print(f"✅ Loaded {len(data)} items from CSV", style="green")
        return data
    
    def _load_json(self, file_path: str) -> List[Dict[str, Any]]:
        """Load JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
        
        # Handle different JSON structures
        if isinstance(json_data, list):
            data = json_data
        elif isinstance(json_data, dict):
            if 'data' in json_data:
                data = json_data['data']
            elif 'items' in json_data:
                data = json_data['items']
            else:
                data = [json_data]
        else:
            raise ValueError("Invalid JSON structure")
        
        # Process each item
        processed_data = []
        for i, item in enumerate(data):
            processed_item = {
                'id': item.get('id', str(i + 1)),
                'input_text': item.get('input_text', '').strip(),
                'description': item.get('description', '').strip(),
                'context': item.get('context', '').strip(),
                'case': item.get('case', '').strip(),
                'priority': item.get('priority', 'normal').strip(),
                'row_number': i + 2,  # +2 for header
                'original_data': item
            }
            
            if processed_item['input_text']:
                processed_data.append(processed_item)
        
        console.print(f"✅ Loaded {len(processed_data)} items from JSON", style="green")
        return processed_data
    
    def _load_jsonlines(self, file_path: str) -> List[Dict[str, Any]]:
        """Load JSON Lines file"""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    item = json.loads(line)
                    
                    processed_item = {
                        'id': item.get('id', str(line_no)),
                        'input_text': item.get('input_text', '').strip(),
                        'description': item.get('description', '').strip(),
                        'context': item.get('context', '').strip(),
                        'case': item.get('case', '').strip(),
                        'priority': item.get('priority', 'normal').strip(),
                        'row_number': line_no + 1,  # +1 for header
                        'original_data': item
                    }
                    
                    if processed_item['input_text']:
                        data.append(processed_item)
                        
                except json.JSONDecodeError as e:
                    console.print(f"⚠️ Skipping invalid JSON at line {line_no}: {e}", style="yellow")
                    continue
        
        console.print(f"✅ Loaded {len(data)} items from JSONL", style="green")
        return data
    
    def _load_text(self, file_path: str) -> List[Dict[str, Any]]:
        """Load plain text file (one query per line)"""
        data = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines và comments
                if not line or line.startswith('#'):
                    continue
                
                processed_item = {
                    'id': str(line_no),
                    'input_text': line,
                    'description': f"Query from line {line_no}",
                    'context': '',
                    'case': '',
                    'priority': 'normal',
                    'row_number': line_no + 1,  # +1 for header
                    'original_data': {'line': line, 'line_number': line_no}
                }
                
                data.append(processed_item)
        
        console.print(f"✅ Loaded {len(data)} items from TXT", style="green")
        return data
    
    def create_sample_csv(self, output_path: str, num_samples: int = 5):
        """Tạo sample CSV file"""
        sample_data = [
            {
                'input_text': 'blue shirts',
                'context': 'Customer looking for clothing',
                'case': 'product_search'
            },
            {
                'input_text': 'show me Arthur Ashe polo shirts',
                'context': 'Customer wants specific brand',
                'case': 'brand_search'
            },
            {
                'input_text': 'find products between 100 and 500 vnd',
                'context': 'Budget-conscious customer',
                'case': 'price_filter'
            },
            {
                'input_text': 'i want sneakers on sale',
                'context': 'Customer looking for deals',
                'case': 'sale_search'
            },
            {
                'input_text': 'từ 100 đến 500 vnd',
                'context': 'Vietnamese customer with budget',
                'case': 'price_filter_vi'
            }
        ]
        
        # Take only requested number of samples
        sample_data = sample_data[:num_samples]
        
        # Write to CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['input_text', 'context', 'case']
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            writer.writeheader()
            writer.writerows(sample_data)
        
        console.print(f"✅ Created sample CSV file: {output_path}", style="green")
    
    def validate_data(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate loaded data"""
        validation_result = {
            'total_items': len(data),
            'valid_items': 0,
            'empty_input_text': 0,
            'missing_fields': [],
            'warnings': []
        }
        
        required_fields = ['id', 'input_text']
        
        for item in data:
            # Check required fields
            missing = [field for field in required_fields if not item.get(field)]
            if missing:
                validation_result['missing_fields'].extend(missing)
                continue
            
            # Check empty input_text
            if not item['input_text'].strip():
                validation_result['empty_input_text'] += 1
                continue
            
            validation_result['valid_items'] += 1
        
        # Add warnings
        if validation_result['empty_input_text'] > 0:
            validation_result['warnings'].append(f"{validation_result['empty_input_text']} items have empty input_text")
        
        return validation_result

# Test function
if __name__ == "__main__":
    # Test the file processor
    processor = FileProcessorService()
    
    # Create sample CSV
    sample_file = "data/input/sample_batch.csv"
    processor.create_sample_csv(sample_file)
    
    # Load and validate
    try:
        data = processor.load_data(sample_file)
        validation = processor.validate_data(data)
        
        print(f"Validation Results: {validation}")
        print(f"Sample data: {data[0] if data else 'No data'}")
        
    except Exception as e:
        print(f"Test failed: {e}")
