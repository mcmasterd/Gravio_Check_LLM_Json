#!/usr/bin/env python3
"""
Main Entry Point - Simple Processor
Clean và simple entry point cho rebuilt system
"""

import argparse
import sys
from pathlib import Path
from services.service_container import ServiceContainer
from services.workflow_orchestrator import WorkflowOrchestrator
from rich.console import Console
from rich.panel import Panel

console = Console()

def main():
    """Main entry point với clean interface"""
    
    parser = argparse.ArgumentParser(description="Shopify MCP Workflow Processor (Rebuilt)")
    parser.add_argument("--config", default="config/settings.yaml", help="Configuration file path")
    parser.add_argument("--start-row", type=int, default=2, help="Start row for processing")
    parser.add_argument("--end-row", type=int, help="End row for processing")
    parser.add_argument("--skip-processed", action="store_true", default=True, help="Skip already processed rows")
    parser.add_argument("--test", action="store_true", help="Test all services connection")
    
    args = parser.parse_args()
    
    try:
        console.print(Panel.fit(
            "🚀 Shopify MCP Workflow Processor (Rebuilt)",
            style="bold blue"
        ))
        
        # Initialize services
        console.print("🏗️ Initializing services...", style="blue")
        service_container = ServiceContainer(args.config)
        orchestrator = WorkflowOrchestrator(service_container)
        
        if args.test:
            # Test mode
            console.print("🧪 Running service tests...", style="blue")
            test_result = orchestrator.test_all_services()
            
            if test_result.success:
                console.print("✅ All services are healthy!", style="green")
                return 0
            else:
                console.print(f"❌ Service test failed: {test_result.error_message}", style="red")
                return 1
        
        else:
            # Processing mode
            console.print("🎯 Starting data processing...", style="blue")
            
            result = orchestrator.process_sheet_data(
                start_row=args.start_row,
                end_row=args.end_row,
                skip_processed=args.skip_processed
            )
            
            if result.success:
                data = result.data
                console.print(f"""
✅ [bold green]Processing completed successfully![/bold green]

📊 [bold]Results Summary:[/bold]
   • Total processed: {data.get('processed_count', 0)}
   • Successful: {data.get('success_count', 0)}
   • Errors: {data.get('error_count', 0)}
   • Success rate: {(data.get('success_count', 0) / max(data.get('processed_count', 1), 1) * 100):.1f}%
                """)
                return 0
            else:
                console.print(f"❌ Processing failed: {result.error_message}", style="red")
                return 1
                
    except KeyboardInterrupt:
        console.print("\n⚠️ Processing interrupted by user", style="yellow")
        return 1
        
    except Exception as e:
        console.print(f"💥 Unexpected error: {str(e)}", style="red")
        return 1

if __name__ == "__main__":
    sys.exit(main())
