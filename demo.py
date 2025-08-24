#!/usr/bin/env python3
"""
Universal Web Action Agent - Demo Script

This script demonstrates the capabilities of the web automation system
with example tasks and mock browser operations.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the core module to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import UniversalWebAgent, AgentConfig
from core.exceptions import WebAutomationError


def setup_logging() -> None:
    """Setup logging for the demo."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def print_demo_banner() -> None:
    """Print the demo banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                Universal Web Action Agent                    ║
║                        DEMO MODE                            ║
║                                                              ║
║  This demo showcases the system's capabilities with         ║
║  mock browser operations and AI reasoning.                  ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_demo_tasks() -> None:
    """Print available demo tasks."""
    tasks = """
Available Demo Tasks:
────────────────────

1. Email Tasks:
   • "send email to demo@example.com about meeting saying 'Hello from the demo!'"
   • "compose email to team@company.com about project update saying 'Project is on track'"
   • "send email to client@business.com about proposal saying 'Here is our proposal'"

2. Complex Tasks:
   • "send email to alice@example.com about tomorrow's meeting saying 'Meeting at 2pm in conference room'"
   • "compose email to bob@team.com about weekly report saying 'Weekly report attached'"

3. Custom Tasks:
   • Enter your own natural language instruction
"""
    print(tasks)


async def run_demo_task(agent: UniversalWebAgent, instruction: str) -> None:
    """Run a single demo task."""
    print(f"\n{'='*60}")
    print(f"Executing: {instruction}")
    print(f"{'='*60}")
    
    try:
        # Execute the task
        result = await agent.execute_task(instruction)
        
        # Display results
        if result.get("success"):
            print("✅ Task completed successfully!")
            print(f"Task: {result.get('task', {})}")
            print()
            print("Provider Results:")
            
            for provider_name, provider_result in result.get("results", {}).items():
                if provider_result.get("success"):
                    print(f"  {provider_name}: ✅ Success")
                    print(f"    Message: {provider_result.get('message', 'N/A')}")
                else:
                    print(f"  {provider_name}: ❌ Failed")
                    print(f"    Error: {provider_result.get('error', 'Unknown error')}")
                print()
            
            print(f"Logs: {len(result.get('logs', []))} log entries")
        else:
            print("❌ Task execution failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Logs: {result.get('logs', [])}")
            
    except Exception as e:
        print(f"❌ Demo task failed: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()


async def interactive_demo() -> None:
    """Run an interactive demo session."""
    print("\n🎯 Interactive Demo Mode")
    print("Type 'quit' to exit, 'help' for available tasks, or enter your instruction.")
    
    while True:
        try:
            instruction = input("\n🤖 Enter your instruction: ").strip()
            
            if instruction.lower() in ['quit', 'exit', 'q']:
                print("👋 Demo session ended. Goodbye!")
                break
                
            elif instruction.lower() in ['help', 'h', '?']:
                print_demo_tasks()
                continue
                
            elif not instruction:
                print("Please enter an instruction or type 'help' for examples.")
                continue
            
            # Create a new agent instance for each task
            config = AgentConfig(
                openai_api_key=os.getenv('OPENAI_API_KEY'),
                headless=True,  # Use headless mode for demo
                timeout=30000,
                log_level='INFO'
            )
            
            agent = UniversalWebAgent(config)
            
            # Run the task
            await run_demo_task(agent, instruction)
            
            # Clean up
            await agent.close()
            
        except KeyboardInterrupt:
            print("\n\n👋 Demo session interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Demo error: {e}")


async def run_preset_demos() -> None:
    """Run a series of preset demo tasks."""
    preset_tasks = [
        "send email to demo@example.com about meeting saying 'Hello from the demo!'",
        "compose email to team@company.com about project update saying 'Project is on track'",
        "send email to client@business.com about proposal saying 'Here is our proposal'"
    ]
    
    print("\n🎬 Running Preset Demo Tasks")
    print("This will demonstrate the system with predefined examples.")
    
    # Create agent instance
    config = AgentConfig(
        openai_api_key=os.getenv('OPENAI_API_KEY'),
        headless=True,  # Use headless mode for demo
        timeout=30000,
        log_level='INFO'
    )
    
    agent = UniversalWebAgent(config)
    
    try:
        for i, task in enumerate(preset_tasks, 1):
            print(f"\n📝 Demo Task {i}/{len(preset_tasks)}")
            await run_demo_task(agent, task)
            
            # Small delay between tasks
            if i < len(preset_tasks):
                print("\n⏳ Waiting 2 seconds before next task...")
                await asyncio.sleep(2)
                
    finally:
        await agent.close()


async def main() -> None:
    """Main demo function."""
    try:
        # Setup
        setup_logging()
        print_demo_banner()
        
        # Check if OpenAI API key is available
        if not os.getenv('OPENAI_API_KEY'):
            print("❌ Error: OPENAI_API_KEY environment variable is required.")
            print("Please set it or create a .env file with your OpenAI API key.")
            print("\nExample .env file:")
            print("OPENAI_API_KEY=your_api_key_here")
            return
        
        print("✅ OpenAI API key configured")
        print("✅ System ready for demo")
        
        # Show demo options
        print("\nChoose demo mode:")
        print("1. Preset demo tasks (automated)")
        print("2. Interactive demo (manual input)")
        print("3. Exit")
        
        while True:
            try:
                choice = input("\nEnter your choice (1-3): ").strip()
                
                if choice == '1':
                    await run_preset_demos()
                    break
                elif choice == '2':
                    await interactive_demo()
                    break
                elif choice == '3':
                    print("👋 Demo cancelled. Goodbye!")
                    break
                else:
                    print("Please enter 1, 2, or 3.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Demo cancelled. Goodbye!")
                break
                
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        if hasattr(e, '__traceback__'):
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
