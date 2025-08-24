#!/usr/bin/env python3
"""
Credential Setup Utility for Universal Web Action Agent

This script helps users set up their email credentials either temporarily
as environment variables or permanently by creating a .env file.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional


def print_banner() -> None:
    """Print the setup banner."""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║              Credential Setup Utility                        ║
║                                                              ║
║  This utility helps you configure email credentials for      ║
║  the Universal Web Action Agent system.                     ║
╚══════════════════════════════════════════════════════════════╝
"""
    print(banner)


def get_user_input(prompt: str, required: bool = True, password: bool = False) -> Optional[str]:
    """Get user input with validation."""
    while True:
        if password:
            import getpass
            value = getpass.getpass(prompt)
        else:
            value = input(prompt).strip()
        
        if not value and required:
            print("❌ This field is required. Please try again.")
            continue
        
        return value if value else None


def setup_openai_key() -> Optional[str]:
    """Set up OpenAI API key."""
    print("\n🔑 OpenAI API Key Setup")
    print("You need an OpenAI API key to use the AI reasoning capabilities.")
    print("Get your key from: https://platform.openai.com/api-keys")
    
    api_key = get_user_input("Enter your OpenAI API key: ", required=True, password=True)
    
    if api_key:
        # Set as environment variable for current session
        os.environ['OPENAI_API_KEY'] = api_key
        print("✅ OpenAI API key set for current session")
        return api_key
    
    return None


def setup_gmail_credentials() -> Optional[Dict[str, str]]:
    """Set up Gmail credentials."""
    print("\n📧 Gmail Credentials Setup")
    print("Note: If you have 2FA enabled, you'll need to use an App Password.")
    print("Create one at: https://myaccount.google.com/apppasswords")
    
    email = get_user_input("Enter your Gmail address: ", required=True)
    if not email:
        return None
    
    password = get_user_input("Enter your Gmail password or app password: ", required=True, password=True)
    if not password:
        return None
    
    credentials = {
        'email': email,
        'password': password
    }
    
    # Set as environment variables for current session
    os.environ['GMAIL_EMAIL'] = email
    os.environ['GMAIL_PASSWORD'] = password
    
    print("✅ Gmail credentials set for current session")
    return credentials


def setup_outlook_credentials() -> Optional[Dict[str, str]]:
    """Set up Outlook credentials."""
    print("\n📧 Outlook Credentials Setup")
    print("Note: If you have 2FA enabled, you may need to use an app password.")
    
    email = get_user_input("Enter your Outlook email address: ", required=True)
    if not email:
        return None
    
    password = get_user_input("Enter your Outlook password or app password: ", required=True, password=True)
    if not password:
        return None
    
    credentials = {
        'email': email,
        'password': password
    }
    
    # Set as environment variables for current session
    os.environ['OUTLOOK_EMAIL'] = email
    os.environ['OUTLOOK_PASSWORD'] = password
    
    print("✅ Outlook credentials set for current session")
    return credentials


def create_env_file(credentials: Dict[str, Any]) -> bool:
    """Create a .env file with the provided credentials."""
    env_content = f"""# OpenAI API Configuration
OPENAI_API_KEY={credentials.get('openai_api_key', 'your_openai_api_key_here')}

# Browser Configuration
HEADLESS=false
TIMEOUT=30000
LOG_LEVEL=INFO

# Gmail Credentials
GMAIL_EMAIL={credentials.get('gmail', {}).get('email', 'your_gmail@gmail.com')}
GMAIL_PASSWORD={credentials.get('gmail', {}).get('password', 'your_gmail_app_password')}

# Outlook Credentials
OUTLOOK_EMAIL={credentials.get('outlook', {}).get('email', 'your_outlook@outlook.com')}
OUTLOOK_PASSWORD={credentials.get('outlook', {}).get('password', 'your_outlook_password')}

# Optional: Screenshot Directory
# SCREENSHOT_DIR=./screenshots
"""
    
    try:
        env_file = Path('.env')
        with open(env_file, 'w') as f:
            f.write(env_content)
        
        print(f"✅ Created .env file at: {env_file.absolute()}")
        print("⚠️  Important: Add .env to your .gitignore to avoid committing credentials!")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False


def show_current_credentials() -> None:
    """Show currently configured credentials."""
    print("\n📋 Current Credentials Status")
    print("=" * 50)
    
    # Check environment variables
    openai_key = os.getenv('OPENAI_API_KEY')
    gmail_email = os.getenv('GMAIL_EMAIL')
    gmail_password = os.getenv('GMAIL_PASSWORD')
    outlook_email = os.getenv('OUTLOOK_EMAIL')
    outlook_password = os.getenv('OUTLOOK_PASSWORD')
    
    print(f"OpenAI API Key: {'✅ Configured' if openai_key else '❌ Not configured'}")
    print(f"Gmail Email: {'✅ Configured' if gmail_email else '❌ Not configured'}")
    print(f"Gmail Password: {'✅ Configured' if gmail_password else '❌ Not configured'}")
    print(f"Outlook Email: {'✅ Configured' if outlook_email else '❌ Not configured'}")
    print(f"Outlook Password: {'✅ Configured' if outlook_password else '❌ Not configured'}")
    
    # Check .env file
    env_file = Path('.env')
    if env_file.exists():
        print(f"\n📁 .env file exists at: {env_file.absolute()}")
    else:
        print("\n📁 No .env file found")


def test_credentials() -> None:
    """Test if the credentials work by trying to import the agent."""
    print("\n🧪 Testing Credentials")
    print("Attempting to import the Universal Web Agent...")
    
    try:
        # Add the core module to the path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from core.agent import UniversalWebAgent, AgentConfig
        
        # Try to create an agent instance
        config = AgentConfig(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            headless=True,
            timeout=30000,
            log_level='INFO'
        )
        
        print("✅ Successfully imported Universal Web Agent")
        print("✅ Credentials appear to be valid")
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        print("This might indicate missing dependencies or incorrect imports.")
        
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        print("This might indicate invalid credentials or configuration issues.")


def main() -> None:
    """Main setup function."""
    print_banner()
    
    credentials = {}
    
    print("Choose setup option:")
    print("1. Setup all credentials (OpenAI + Gmail + Outlook)")
    print("2. Setup OpenAI API key only")
    print("3. Setup email credentials only (Gmail + Outlook)")
    print("4. Show current credentials status")
    print("5. Test credentials")
    print("6. Create .env file")
    print("7. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-7): ").strip()
            
            if choice == '1':
                # Setup all credentials
                openai_key = setup_openai_key()
                if openai_key:
                    credentials['openai_api_key'] = openai_key
                
                gmail_creds = setup_gmail_credentials()
                if gmail_creds:
                    credentials['gmail'] = gmail_creds
                
                outlook_creds = setup_outlook_credentials()
                if outlook_creds:
                    credentials['outlook'] = outlook_creds
                
                print("\n✅ All credentials configured!")
                
            elif choice == '2':
                # Setup OpenAI only
                openai_key = setup_openai_key()
                if openai_key:
                    credentials['openai_api_key'] = openai_key
                
            elif choice == '3':
                # Setup email credentials only
                gmail_creds = setup_gmail_credentials()
                if gmail_creds:
                    credentials['gmail'] = gmail_creds
                
                outlook_creds = setup_outlook_credentials()
                if outlook_creds:
                    credentials['outlook'] = outlook_creds
                
            elif choice == '4':
                # Show current status
                show_current_credentials()
                
            elif choice == '5':
                # Test credentials
                test_credentials()
                
            elif choice == '6':
                # Create .env file
                if credentials:
                    create_env_file(credentials)
                else:
                    print("❌ No credentials configured yet. Please setup credentials first.")
                
            elif choice == '7':
                # Exit
                print("👋 Setup utility closed. Goodbye!")
                break
                
            else:
                print("Please enter a number between 1 and 7.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Setup utility interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Final summary
    if credentials:
        print("\n📋 Setup Summary:")
        print("=" * 30)
        
        if 'openai_api_key' in credentials:
            print("✅ OpenAI API key configured")
        
        if 'gmail' in credentials:
            print("✅ Gmail credentials configured")
            
        if 'outlook' in credentials:
            print("✅ Outlook credentials configured")
        
        print("\n💡 Next steps:")
        print("1. Test your setup: python demo.py")
        print("2. Run the main system: python main.py --help")
        print("3. Start the API server: python api.py")


if __name__ == "__main__":
    main()
