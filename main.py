#!/usr/bin/env python3
"""
Universal Web Action Agent - Main CLI Interface

This is the main entry point for the web automation system.
It provides a command-line interface for executing tasks across
multiple web service providers.
"""

import asyncio
import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

# Add the core module to the path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import UniversalWebAgent, AgentConfig
from core.exceptions import WebAutomationError


def setup_logging(verbose: bool = False) -> None:
    """Setup logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('web_agent.log')
        ]
    )


def load_config() -> Dict[str, Any]:
    """Load configuration from environment variables or config file."""
    config = {}
    
    # Try to load from .env file
    env_file = Path('.env')
    if env_file.exists():
        from dotenv import load_dotenv
        load_dotenv()
    
    # Load from environment variables
    config['openai_api_key'] = os.getenv('OPENAI_API_KEY')
    config['headless'] = os.getenv('HEADLESS', 'false').lower() == 'true'
    config['timeout'] = int(os.getenv('TIMEOUT', '30000'))
    config['log_level'] = os.getenv('LOG_LEVEL', 'INFO')
    
    return config


def validate_config(config: Dict[str, Any]) -> None:
    """Validate that required configuration is present."""
    if not config.get('openai_api_key'):
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it or create a .env file."
        )


def print_banner() -> None:
    """Print the application banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                Universal Web Action Agent                    ║
║                                                              ║
║  Automate tasks across multiple web services using          ║
║  natural language instructions and AI reasoning.            ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def print_examples() -> None:
    """Print example usage commands."""
    examples = """
Examples:
  python main.py "send email to alice@example.com about meeting saying 'Hi Alice, let's meet at 2pm'"
  python main.py "upload document to google drive"
  python main.py "schedule meeting with bob tomorrow at 3pm"
  python main.py --verbose "send email to team about project update"
  
Environment Variables:
  OPENAI_API_KEY    Your OpenAI API key (required)
  HEADLESS          Set to 'true' for headless browser mode
  TIMEOUT           Browser timeout in milliseconds (default: 30000)
  LOG_LEVEL         Logging level (default: INFO)
"""
    print(examples)


async def main() -> None:
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Universal Web Action Agent - Execute tasks across web services",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=print_examples()
    )
    
    parser.add_argument(
        "instruction",
        nargs="?",
        help="Natural language instruction describing the task to perform"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run browser in headless mode"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=30000,
        help="Browser timeout in milliseconds"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="Path to configuration file"
    )
    
    parser.add_argument(
        "--examples",
        action="store_true",
        help="Show example usage"
    )
    
    args = parser.parse_args()
    
    # Show examples if requested
    if args.examples:
        print_examples()
        return
    
    # Show help if no instruction provided
    if not args.instruction:
        parser.print_help()
        return
    
    try:
        # Setup logging
        setup_logging(args.verbose)
        logger = logging.getLogger(__name__)
        
        # Print banner
        print_banner()
        
        # Load and validate configuration
        config = load_config()
        if args.headless:
            config['headless'] = True
        if args.timeout:
            config['timeout'] = args.timeout
            
        validate_config(config)
        
        # Create agent configuration
        agent_config = AgentConfig(
            openai_api_key=config['openai_api_key'],
            headless=config['headless'],
            timeout=config['timeout'],
            log_level=config['log_level']
        )
        
        # Initialize the agent
        logger.info("Initializing Universal Web Action Agent...")
        agent = UniversalWebAgent(agent_config)
        
        # Set up credentials for providers (in a real app, these would come from secure storage)
        # For demo purposes, we'll use environment variables
        gmail_email = os.getenv('GMAIL_EMAIL')
        gmail_password = os.getenv('GMAIL_PASSWORD')
        outlook_email = os.getenv('OUTLOOK_EMAIL')
        outlook_password = os.getenv('OUTLOOK_PASSWORD')
        
        if gmail_email and gmail_password:
            agent.providers['gmail'].set_credentials({
                'email': gmail_email,
                'password': gmail_password
            })
            logger.info("Gmail credentials configured")
            
        if outlook_email and outlook_password:
            agent.providers['outlook'].set_credentials({
                'email': outlook_email,
                'password': outlook_password
            })
            logger.info("Outlook credentials configured")
        
        # Execute the task
        logger.info(f"Executing task: {args.instruction}")
        result = await agent.execute_task(args.instruction)
        
        # Display results
        print("\n" + "=" * 60)
        print("TASK EXECUTION RESULTS")
        print("=" * 60)
        
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
            
            print(f"Logs: {result.get('logs', [])}")
        else:
            print("❌ Task execution failed!")
            print(f"Error: {result.get('error', 'Unknown error')}")
            print(f"Logs: {result.get('logs', [])}")
        
        print("=" * 60)
        
        # Clean up
        await agent.close()
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
        
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
