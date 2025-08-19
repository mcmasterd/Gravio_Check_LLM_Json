#!/usr/bin/env python3
"""
Google Sheets service for batch processing
"""

import os
import time
from typing import List, Dict, Any, Optional, Tuple
import gspread
from google.oauth2.service_account import Credentials
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class GoogleSheetsService:
    """Service để interact với Google Sheets"""
    
    def __init__(self, credentials_file: str, sheet_id: str, sheet_name: str = "Detail"):
        self.credentials_file = credentials_file
        self.sheet_id = sheet_id
        self.sheet_name = sheet_name
        self.client = None
        self.worksheet = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup Google Sheets client"""
        try:
            # Define scopes
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Load credentials
            credentials = Credentials.from_service_account_file(
                self.credentials_file,
                scopes=scopes
            )
            
            # Create client
            self.client = gspread.authorize(credentials)
            
            # Open worksheet
            spreadsheet = self.client.open_by_key(self.sheet_id)
            self.worksheet = spreadsheet.worksheet(self.sheet_name)
            
            console.print(f"✅ Connected to Google Sheet: {self.sheet_name}", style="green")
            
        except Exception as e:
            console.print(f"❌ Failed to setup Google Sheets client: {e}", style="red")
            raise
    
    def get_input_data(self, start_row: int = 2, end_row: Optional[int] = None) -> List[Dict[str, Any]]:
        """Đọc input data từ sheet bao gồm cả kết quả đã xử lý"""
        try:
            # Get all values if end_row not specified
            if end_row is None:
                # Get all data from start_row to the last row with data
                all_values = self.worksheet.get_all_values()
                if len(all_values) < start_row:
                    return []
                values = all_values[start_row-1:]  # -1 because get_all_values is 0-indexed
            else:
                # Get specific range - mở rộng để bao gồm cột D..H (do map lại cột)
                range_name = f"A{start_row}:H{end_row}"
                values = self.worksheet.get(range_name)
                if not values:
                    return []
            
            # Convert to list of dictionaries
            input_data = []
            for i, row in enumerate(values):
                if len(row) >= 2 and row[1].strip():  # Có ít nhất ID và input_text
                    item = {
                        'row_number': start_row + i,
                        'id': row[0] if len(row) > 0 else str(start_row + i),
                        'input_text': row[1] if len(row) > 1 else '',
                        'case': row[2] if len(row) > 2 else '',
                        'json_output': row[3] if len(row) > 3 else '',       # Cột D (LLM JSON)
                        'api_request': row[4] if len(row) > 4 else '',       # Cột E (API request JSON)
                        'api_response': row[5] if len(row) > 5 else '',      # Cột F (API response)
                        'filtered_response': row[6] if len(row) > 6 else '', # Cột G (summary/filtered)
                        'model_info': row[7] if len(row) > 7 else ''         # Cột H
                    }
                    input_data.append(item)
            
            console.print(f"📊 Found {len(input_data)} items to process", style="blue")
            return input_data
            
        except Exception as e:
            console.print(f"❌ Failed to read input data: {e}", style="red")
            raise
    
    def update_single_row(self, row_number: int, data: Dict[str, str], delay: float = 0.1):
        """Update một row với kết quả processing"""
        try:
            # Map data to columns (D..H)
            updates = []
            
            # Column D: JSON Output
            if 'json_output' in data:
                updates.append({
                    'range': f'D{row_number}',
                    'values': [[data['json_output']]]
                })
            # Column E: API Request (formatted)
            if 'api_request' in data:
                updates.append({
                    'range': f'E{row_number}',
                    'values': [[data['api_request']]]
                })
            # Column F: API Response
            if 'api_response' in data:
                updates.append({
                    'range': f'F{row_number}',
                    'values': [[data['api_response']]]
                })
            # Column G: Filtered/Summary
            if 'filtered_response' in data:
                updates.append({
                    'range': f'G{row_number}',
                    'values': [[data['filtered_response']]]
                })
            # Column H: Model Info
            if 'model_info' in data:
                updates.append({
                    'range': f'H{row_number}',
                    'values': [[data['model_info']]]
                })
            
            # Batch update
            if updates:
                self.worksheet.batch_update(updates)
                
            # Rate limiting
            time.sleep(delay)
            
        except Exception as e:
            console.print(f"❌ Failed to update row {row_number}: {e}", style="red")
            raise
    
    def batch_update_rows(self, updates: List[Dict[str, Any]], delay: float = 0.5):
        """Batch update multiple rows"""
        try:
            # Group updates by range
            batch_updates = []
            
            for update in updates:
                row_number = update['row_number']
                data = update['data']
                
                # Add each column update
                if 'json_output' in data:
                    batch_updates.append({
                        'range': f'D{row_number}',
                        'values': [[data['json_output']]]
                    })
                if 'api_request' in data:
                    batch_updates.append({
                        'range': f'E{row_number}',
                        'values': [[data['api_request']]]
                    })
                if 'api_response' in data:
                    batch_updates.append({
                        'range': f'F{row_number}',
                        'values': [[data['api_response']]]
                    })
                if 'filtered_response' in data:
                    batch_updates.append({
                        'range': f'G{row_number}',
                        'values': [[data['filtered_response']]]
                    })
                if 'model_info' in data:
                    batch_updates.append({
                        'range': f'H{row_number}',
                        'values': [[data['model_info']]]
                    })
            
            # Execute batch update
            if batch_updates:
                self.worksheet.batch_update(batch_updates)
                console.print(f"✅ Updated {len(updates)} rows", style="green")
            
            # Rate limiting
            time.sleep(delay)
            
        except Exception as e:
            console.print(f"❌ Failed to batch update: {e}", style="red")
            raise
    
    def get_last_row_with_data(self, column: str = 'B') -> int:
        """Tìm row cuối cùng có dữ liệu trong column"""
        try:
            # Get all values in column
            column_values = self.worksheet.col_values(ord(column.upper()) - ord('A') + 1)
            
            # Find last non-empty cell
            last_row = 0
            for i, value in enumerate(column_values):
                if value.strip():
                    last_row = i + 1
            
            return last_row
            
        except Exception as e:
            console.print(f"❌ Failed to get last row: {e}", style="red")
            return 0
    
    def clear_output_columns(self, start_row: int, end_row: int):
        """Clear output columns (D..H) trong range"""
        try:
            # Clear columns D to H
            ranges_to_clear = [
                f'D{start_row}:H{end_row}'
            ]
            
            for range_name in ranges_to_clear:
                self.worksheet.batch_clear(ranges_to_clear)
            
            console.print(f"🧹 Cleared output columns from row {start_row} to {end_row}", style="yellow")
            
        except Exception as e:
            console.print(f"❌ Failed to clear columns: {e}", style="red")
            raise
    
    def add_headers_if_missing(self):
        """Thêm headers nếu chưa có"""
        try:
            # Check if headers exist
            first_row = self.worksheet.row_values(1)
            
            expected_headers = ['ID', 'Input Text', 'Case', 'JSON Output', 'API Request', 'API Response', 'Filtered Response', 'Model Info']
            
            if not first_row or len(first_row) < len(expected_headers):
                # Add headers
                self.worksheet.update('A1:H1', [expected_headers])
                console.print("✅ Added headers to sheet", style="green")
            
        except Exception as e:
            console.print(f"❌ Failed to add headers: {e}", style="red")
            raise
    
    def get_sheet_info(self) -> Dict[str, Any]:
        """Lấy thông tin về sheet"""
        try:
            info = {
                'sheet_id': self.sheet_id,
                'sheet_name': self.sheet_name,
                'last_row_with_data': self.get_last_row_with_data(),
                'row_count': self.worksheet.row_count,
                'col_count': self.worksheet.col_count
            }
            
            return info
            
        except Exception as e:
            console.print(f"❌ Failed to get sheet info: {e}", style="red")
            return {}
    
    def get_existing_data_hash(self, start_row: int = 2, end_row: Optional[int] = None) -> Dict[str, int]:
        """Lấy hash của existing data để check duplicate (input_text + context -> row_number)"""
        try:
            # Get all data from sheet
            if end_row is None:
                all_values = self.worksheet.get_all_values()
                if len(all_values) < start_row:
                    return {}
                values = all_values[start_row-1:]  # -1 vì get_all_values là 0-indexed
                rows_to_check = range(start_row, len(all_values) + 1)
            else:
                range_name = f"A{start_row}:C{end_row}"
                values = self.worksheet.get(range_name)
                if not values:
                    return {}
                rows_to_check = range(start_row, end_row + 1)
            
            # Create hash map: "input_text|context" -> row_number
            data_hash = {}
            for i, row in enumerate(values):
                if len(row) >= 2 and row[1].strip():  # Có input_text
                    input_text = row[1].strip() if len(row) > 1 else ''
                    context = row[2].strip() if len(row) > 2 else ''
                    
                    # Tạo key unique từ input_text + context
                    key = f"{input_text}|{context}"
                    data_hash[key] = list(rows_to_check)[i]
            
            console.print(f"📊 Found {len(data_hash)} existing unique records", style="blue")
            return data_hash
            
        except Exception as e:
            console.print(f"❌ Failed to get existing data hash: {e}", style="red")
            return {}
    
    def get_processed_rows(self, start_row: int = 2, end_row: Optional[int] = None) -> set:
        """Lấy danh sách các row đã được xử lý (có dữ liệu ở column D)"""
        try:
            # Get column D (JSON Output) để check xem row nào đã xử lý
            if end_row is None:
                column_d_values = self.worksheet.col_values(4)  # Column D
                processed_rows = set()
                for i, value in enumerate(column_d_values[start_row-1:], start=start_row):
                    if value and value.strip() and not value.strip().startswith('JSON Output'):
                        processed_rows.add(i)
            else:
                range_name = f"D{start_row}:D{end_row}"
                values = self.worksheet.get(range_name)
                processed_rows = set()
                for i, row in enumerate(values):
                    if row and row[0] and row[0].strip():
                        processed_rows.add(start_row + i)
            
            console.print(f"📊 Found {len(processed_rows)} already processed rows", style="blue")
            return processed_rows
            
        except Exception as e:
            console.print(f"❌ Failed to get processed rows: {e}", style="red")
            return set()
    
    def append_new_data(self, new_data: List[Dict[str, Any]], avoid_duplicates: bool = True) -> Dict[str, Any]:
        """Thêm data mới vào cuối sheet, tránh duplicate nếu được yêu cầu"""
        try:
            # Get existing data hash nếu cần tránh duplicate
            existing_hash = {}
            if avoid_duplicates:
                existing_hash = self.get_existing_data_hash()
            
            # Get current last row
            current_last_row = self.get_last_row_with_data()
            next_id = current_last_row  # ID tự tăng
            
            # Filter out duplicates
            unique_data = []
            duplicates_count = 0
            
            for item in new_data:
                input_text = item.get('input_text', '').strip()
                context = item.get('context', '').strip()
                key = f"{input_text}|{context}"
                
                if avoid_duplicates and key in existing_hash:
                    duplicates_count += 1
                    console.print(f"⚠️ Skipping duplicate: {input_text[:50]}...", style="yellow")
                    continue
                
                unique_data.append(item)
            
            if not unique_data:
                console.print("ℹ️ No new unique data to add", style="cyan")
                return {
                    "status": "success",
                    "added_rows": 0,
                    "duplicate_skipped": duplicates_count,
                    "start_row": current_last_row + 1
                }
            
            # Prepare batch updates
            batch_updates = []
            for i, item in enumerate(unique_data):
                row_number = current_last_row + 1 + i
                current_id = next_id + i
                
                batch_updates.append({
                    'range': f'A{row_number}:C{row_number}',
                    'values': [[
                        str(current_id),
                        item.get('input_text', ''),
                        item.get('context', '')
                    ]]
                })
                
                # Batch update mỗi 50 rows
                if len(batch_updates) >= 50:
                    self.worksheet.batch_update(batch_updates)
                    batch_updates = []
                    time.sleep(0.5)
            
            # Final batch update
            if batch_updates:
                self.worksheet.batch_update(batch_updates)
            
            console.print(f"✅ Added {len(unique_data)} new rows, skipped {duplicates_count} duplicates", style="green")
            
            return {
                "status": "success",
                "added_rows": len(unique_data),
                "duplicate_skipped": duplicates_count,
                "start_row": current_last_row + 1,
                "end_row": current_last_row + len(unique_data)
            }
            
        except Exception as e:
            console.print(f"❌ Failed to append new data: {e}", style="red")
            return {"status": "failed", "reason": str(e)}
    
    def get_unprocessed_data(self, start_row: int = 2, end_row: Optional[int] = None) -> List[Dict[str, Any]]:
        """Lấy data chưa được xử lý (chưa có JSON Output)"""
        try:
            # Get all input data
            all_data = self.get_input_data(start_row, end_row)
            
            # Get processed rows
            processed_rows = self.get_processed_rows(start_row, end_row)
            
            # Filter unprocessed data
            unprocessed_data = []
            for item in all_data:
                if item['row_number'] not in processed_rows:
                    unprocessed_data.append(item)
            
            console.print(f"📊 Found {len(unprocessed_data)} unprocessed items out of {len(all_data)} total", style="blue")
            return unprocessed_data
            
        except Exception as e:
            console.print(f"❌ Failed to get unprocessed data: {e}", style="red")
            return []
