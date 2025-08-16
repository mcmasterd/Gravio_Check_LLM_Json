#!/usr/bin/env python3
"""
LLM-Based Keyword Extractor Service (Python Version)

Sử dụng LLM để extract keywords thông minh thay vì regex patterns
Cung cấp hiểu biết context và intent tốt hơn
"""

import json
import os
import sys
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from openai import OpenAI
import argparse
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
import time

# Load environment variables from .env file
load_dotenv()

# Rich console for beautiful output
console = Console()

@dataclass
class KeywordExtractionResult:
    """Kết quả trích xuất keywords"""
    keywords: List[str]
    filters: Dict[str, Any]
    clean_query: str
    confidence: float
    reasoning: str

class LLMKeywordExtractor:
    """LLM-based keyword extractor using OpenAI GPT 4o mini"""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize with OpenAI API key"""
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            console.print("❌ [ERROR] OPENAI_API_KEY not found in environment variables or .env file", style="red")
            console.print("💡 [TIP] Create a .env file with: OPENAI_API_KEY='your-key-here'", style="yellow")
            console.print("💡 [TIP] Or set environment variable: $env:OPENAI_API_KEY='your-key-here'", style="yellow")
            sys.exit(1)
        
        self.client = OpenAI(api_key=self.api_key)
        
    def extract_keywords(
        self, 
        query: str, 
        language: str = "auto-detect",
        include_filters: bool = True,
        preserve_brands: bool = True
    ) -> KeywordExtractionResult:
        """
        Extract keywords using LLM with context understanding
        
        Args:
            query: User input query
            language: Language for processing
            include_filters: Whether to include filters
            preserve_brands: Whether to preserve brand names
            
        Returns:
            KeywordExtractionResult with extracted data
        """
        
        prompt = f"""You are an expert e-commerce keyword extractor.

🎯 MISSION: Extract meaningful product search keywords from user queries.

📝 QUERY: "{query}"
🌍 LANGUAGE: {language}

🎯 EXTRACTION RULES:
1. **REMOVE** conversational words: "i am", "i want", "can you", "help me", "show me"
2. **REMOVE** action words: "find", "search", "look", "get", "give me"
3. **REMOVE** filler words: "some", "any", "please", "thanks"
4. **KEEP** product keywords: "shirt", "dress", "shoes", "watch"
5. **KEEP** attributes: "blue", "red", "large", "small", "cotton"
6. **KEEP** brands: "Nike", "Adidas", "Arthur Ashe"
7. **KEEP** sale terms: "sale", "discount", "promotion"
8. **UNDERSTAND** context and intent
9. **HANDLE** negation: "not interested in" → remove
10. **NORMALIZE** variations: "mini-skirt" → "mini skirt"

🔍 EXAMPLES:

Input: "i am looking for blue shirts"
Output: {{
  "keywords": ["blue", "shirts"],
  "filters": {{
    "colors": ["blue"],
    "productType": "shirts"
  }},
  "cleanQuery": "blue shirts"
}}

Input: "can you find me some sale items"
Output: {{
  "keywords": ["sale", "items"],
  "filters": {{
    "sales": ["sale"]
  }},
  "cleanQuery": "sale items"
}}

Input: "i am not interested in red dresses"
Output: {{
  "keywords": [],
  "filters": {{}},
  "cleanQuery": "",
  "reasoning": "negative intent detected"
}}

Input: "show me Arthur Ashe polo shirts"
Output: {{
  "keywords": ["Arthur Ashe", "polo", "shirts"],
  "filters": {{
    "brands": ["Arthur Ashe"],
    "productType": "polo shirts"
  }},
  "cleanQuery": "Arthur Ashe polo shirts"
}}

Input: "i want mini-skirts under 300 vnd"
Output: {{
  "keywords": ["mini skirts"],
  "filters": {{
    "price": {{"max": 300}},
    "productType": "mini skirts"
  }},
  "cleanQuery": "mini skirts"
}}

Input: "help me find products priced between 67 vnd and 200 vnd"
Output: {{
  "keywords": ["products"],
  "filters": {{
    "price": {{"min": 67, "max": 200}}
  }},
  "cleanQuery": "products"
}}

Input: "show me items from 100 to 500 vnd"
Output: {{
  "keywords": ["items"],
  "filters": {{
    "price": {{"min": 100, "max": 500}}
  }},
  "cleanQuery": "items"
}}

Input: "find products between $50 and $200"
Output: {{
  "keywords": ["products"],
  "filters": {{
    "price": {{"min": 50, "max": 200}}
  }},
  "cleanQuery": "products"
}}

Input: "i want items priced from 150 vnd to 300 vnd"
Output: {{
  "keywords": ["items"],
  "filters": {{
    "price": {{"min": 150, "max": 300}}
  }},
  "cleanQuery": "items"
}}

Input: "search for products in the range of 80-120 vnd"
Output: {{
  "keywords": ["products"],
  "filters": {{
    "price": {{"min": 80, "max": 120}}
  }},
  "cleanQuery": "products"
}}

Input: "từ 100 đến 500 vnd"
Output: {{
  "keywords": [],
  "filters": {{
    "price": {{"min": 100, "max": 500}}
  }},
  "cleanQuery": "",
  "reasoning": "Vietnamese price range detected"
}}

📋 OUTPUT FORMAT (JSON only):
{{
  "keywords": ["array", "of", "keywords"],
  "filters": {{
    "colors": ["color1", "color2"],
    "sizes": ["size1", "size2"],
    "brands": ["brand1", "brand2"],
    "productType": "product_type",
    "sales": ["sale_term1", "sale_term2"],
    "price": {{"min": number, "max": number}},
    "materials": ["material1", "material2"]
  }},
  "cleanQuery": "cleaned search query",
  "confidence": 0.95,
  "reasoning": "explanation of extraction"
}}

Now extract keywords from this query:"""

        try:
            # Show processing animation
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                task = progress.add_task("🤖 Processing with GPT 4o mini...", total=None)
                
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",  # Using GPT 4o mini
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    # temperature=0.1,
                    max_completion_tokens = 500
                    # max_tokens=500  # Using standard max_tokens parameter
                )
                
                progress.remove_task(task)
            
            # Extract response content
            response_content = response.choices[0].message.content
            
            # Kiểm tra nếu response rỗng hoặc None
            if not response_content:
                console.print("❌ [API ERROR] Empty response from API", style="red")
                return KeywordExtractionResult(
                    keywords=[],
                    filters={},
                    clean_query=query,
                    confidence=0.5,
                    reasoning='fallback to original query due to empty API response'
                )
            
            response_content = response_content.strip()
            
            # Log response để debug
            console.print(f"🔍 [DEBUG] Raw response: {response_content[:200]}...", style="dim")
            
            # Clean the response to extract JSON
            cleaned_response = response_content
            
            # Remove markdown code blocks if present
            if cleaned_response.startswith('```json') and cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[7:-3].strip()
            elif cleaned_response.startswith('```') and cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[3:-3].strip()
            
            # Try to find JSON object in the text if it's mixed with other content
            import re
            json_match = re.search(r'\{[\s\S]*\}', cleaned_response)
            if json_match:
                cleaned_response = json_match.group(0)
            
            result_dict = json.loads(cleaned_response)
            
            # Create result object
            result = KeywordExtractionResult(
                keywords=result_dict.get('keywords', []),
                filters=result_dict.get('filters', {}),
                clean_query=result_dict.get('clean_query', result_dict.get('cleanQuery', '')),
                confidence=result_dict.get('confidence', 0.8),
                reasoning=result_dict.get('reasoning', '')
            )
            
            console.print(f"✅ [SUCCESS] Keywords extracted with confidence: {result.confidence:.2f}", style="green")
            return result
            
        except json.JSONDecodeError as e:
            console.print(f"❌ [JSON ERROR] Failed to parse response: {e}", style="red")
            console.print(f"📄 [RAW RESPONSE] {response_content}", style="dim")
            return KeywordExtractionResult(
                keywords=[],
                filters={},
                clean_query=query,
                confidence=0.5,
                reasoning='fallback to original query due to JSON parse error'
            )
        except ValueError as e:
            console.print(f"❌ [VALUE ERROR] {e}", style="red")
            return KeywordExtractionResult(
                keywords=[],
                filters={},
                clean_query=query,
                confidence=0.5,
                reasoning='fallback to original query due to empty or invalid API response'
            )
        except Exception as e:
            console.print(f"❌ [API ERROR] {e}", style="red")
            return KeywordExtractionResult(
                keywords=[],
                filters={},
                clean_query=query,
                confidence=0.5,
                reasoning='fallback to original query due to API error'
            )

def display_result(result: KeywordExtractionResult, query: str):
    """Display extraction results in beautiful format"""
    
    # Main result panel
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        f"🎯 Keyword Extraction Results",
        style="bold blue"
    ))
    
    # Input query
    console.print(Panel(
        f"📝 Original Query: [bold cyan]{query}[/bold cyan]",
        title="Input",
        border_style="cyan"
    ))
    
    # Keywords table
    if result.keywords:
        keyword_table = Table(title="🔑 Extracted Keywords", show_header=True, header_style="bold magenta")
        keyword_table.add_column("Index", style="dim", width=6)
        keyword_table.add_column("Keyword", style="bold")
        
        for i, keyword in enumerate(result.keywords, 1):
            keyword_table.add_row(str(i), keyword)
        
        console.print(keyword_table)
    else:
        console.print("🚫 No keywords extracted", style="yellow")
    
    # Filters table
    if result.filters:
        filter_table = Table(title="🎛️ Extracted Filters", show_header=True, header_style="bold green")
        filter_table.add_column("Filter Type", style="bold")
        filter_table.add_column("Values", style="cyan")
        
        for filter_type, values in result.filters.items():
            if isinstance(values, list):
                values_str = ", ".join(str(v) for v in values)
            elif isinstance(values, dict):
                values_str = json.dumps(values, indent=2)
            else:
                values_str = str(values)
            
            filter_table.add_row(filter_type, values_str)
        
        console.print(filter_table)
    else:
        console.print("🚫 No filters extracted", style="yellow")
    
    # Clean query and metadata
    metadata_table = Table(title="📊 Metadata", show_header=True, header_style="bold yellow")
    metadata_table.add_column("Property", style="bold")
    metadata_table.add_column("Value", style="white")
    
    metadata_table.add_row("Clean Query", result.clean_query or "N/A")
    metadata_table.add_row("Confidence", f"{result.confidence:.2%}")
    metadata_table.add_row("Reasoning", result.reasoning or "N/A")
    
    console.print(metadata_table)

def interactive_mode():
    """Interactive mode for testing keyword extraction"""
    
    console.print(Panel.fit(
        "🚀 LLM Keyword Extractor - Interactive Mode",
        style="bold blue"
    ))
    
    console.print("""
📋 [bold]Available Commands:[/bold]
• [cyan]Enter your query[/cyan] - Extract keywords
• [yellow]quit/exit[/yellow] - Exit program
• [green]help[/green] - Show this help
• [magenta]clear[/magenta] - Clear screen

💡 [bold]Example queries:[/bold]
• "i am looking for blue shirts"
• "show me Arthur Ashe polo shirts"  
• "find products between 100 and 500 vnd"
• "từ 100 đến 500 vnd"
    """)
    
    extractor = LLMKeywordExtractor()
    
    while True:
        try:
            console.print("\n" + "-"*50)
            query = Prompt.ask("🔍 [bold cyan]Enter your search query[/bold cyan]")
            
            if not query.strip():
                continue
                
            if query.lower() in ['quit', 'exit', 'q']:
                console.print("👋 Goodbye!", style="bold yellow")
                break
            elif query.lower() == 'help':
                console.print("""
📋 [bold]Available Commands:[/bold]
• [cyan]Enter your query[/cyan] - Extract keywords
• [yellow]quit/exit[/yellow] - Exit program
• [green]help[/green] - Show this help
• [magenta]clear[/magenta] - Clear screen
                """)
                continue
            elif query.lower() == 'clear':
                os.system('cls' if os.name == 'nt' else 'clear')
                continue
            
            # Extract keywords
            result = extractor.extract_keywords(query)
            
            # Display results
            display_result(result, query)
            
            # Ask if user wants to see JSON output
            show_json = Prompt.ask("\n📄 Show JSON output?", choices=["y", "n"], default="n")
            if show_json.lower() == 'y':
                json_output = asdict(result)
                console.print(Panel(
                    json.dumps(json_output, indent=2, ensure_ascii=False),
                    title="JSON Output",
                    border_style="dim"
                ))
            
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="bold yellow")
            break
        except Exception as e:
            console.print(f"❌ [ERROR] {e}", style="red")

def batch_mode(input_file: str, output_file: str = None):
    """Batch processing mode"""
    
    console.print(f"📂 Processing batch file: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]
        
        if not queries:
            console.print("❌ No queries found in file", style="red")
            return
        
        extractor = LLMKeywordExtractor()
        results = []
        
        with Progress(console=console) as progress:
            task = progress.add_task("Processing queries...", total=len(queries))
            
            for i, query in enumerate(queries):
                console.print(f"\n🔍 Processing: {query}")
                result = extractor.extract_keywords(query)
                
                result_dict = asdict(result)
                result_dict['original_query'] = query
                results.append(result_dict)
                
                display_result(result, query)
                progress.advance(task)
        
        # Save results if output file specified
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            console.print(f"💾 Results saved to: {output_file}", style="green")
        
    except FileNotFoundError:
        console.print(f"❌ File not found: {input_file}", style="red")
    except Exception as e:
        console.print(f"❌ Error processing batch: {e}", style="red")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="LLM-based Keyword Extractor using GPT 4o mini",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python llm_keyword_extractor.py                           # Interactive mode
  python llm_keyword_extractor.py -q "blue shirts"          # Single query
  python llm_keyword_extractor.py -f queries.txt            # Batch mode
  python llm_keyword_extractor.py -f queries.txt -o results.json
        """
    )
    
    parser.add_argument('-q', '--query', help='Single query to process')
    parser.add_argument('-f', '--file', help='File containing queries (one per line)')
    parser.add_argument('-o', '--output', help='Output file for batch results (JSON)')
    parser.add_argument('--api-key', help='OpenAI API key (or use OPENAI_API_KEY env var)')
    
    args = parser.parse_args()
    
    # Header
    console.print(Panel.fit(
        "🤖 LLM Keyword Extractor\n[dim]Powered by GPT 4o mini[/dim]",
        style="bold blue"
    ))
    
    if args.query:
        # Single query mode
        extractor = LLMKeywordExtractor(args.api_key)
        result = extractor.extract_keywords(args.query)
        display_result(result, args.query)
        
        # Show JSON if requested
        json_output = asdict(result)
        console.print(Panel(
            json.dumps(json_output, indent=2, ensure_ascii=False),
            title="JSON Output",
            border_style="dim"
        ))
        
    elif args.file:
        # Batch mode
        batch_mode(args.file, args.output)
        
    else:
        # Interactive mode
        interactive_mode()

if __name__ == "__main__":
    main()
