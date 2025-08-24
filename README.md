# Universal Web Action Agent

A sophisticated web automation system that uses AI reasoning to execute tasks across multiple web service providers with highly variable UIs.

## 🚀 Features

- **Natural Language Processing**: Accept natural language instructions (e.g., "Send an email to Alice about the meeting at 2pm")
- **AI-Powered Reasoning**: Uses LLM (GPT-4) to interpret instructions and generate DOM interaction steps
- **Multi-Provider Support**: Works with Gmail, Outlook, and extensible to other services
- **Browser Automation**: Built on Playwright for reliable web automation
- **UI Analysis**: Dynamic UI understanding using LLM reasoning
- **Error Recovery**: Robust error handling and recovery mechanisms
- **CLI & API**: Both command-line interface and FastAPI endpoints

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input    │───▶│  Task Parser    │───▶│  LLM Reasoning  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  UI Analyzer    │◀───│  Browser Ctrl   │───▶│  Providers      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                        ┌─────────────────┐
                        │  Playwright     │
                        │  Browser        │
                        └─────────────────┘
```

## 📦 Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd task2
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Playwright browsers**:
   ```bash
   playwright install
   ```

5. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

## ⚙️ Configuration

Create a `.env` file with the following variables:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional
HEADLESS=false
TIMEOUT=30000
LOG_LEVEL=INFO

# Email credentials (for real automation)
GMAIL_EMAIL=your_gmail@gmail.com
GMAIL_PASSWORD=your_gmail_password
OUTLOOK_EMAIL=your_outlook@outlook.com
OUTLOOK_PASSWORD=your_outlook_password
```

## 🚀 Usage

### Command Line Interface

```bash
# Basic usage
python main.py "send email to alice@example.com about meeting saying 'Hi Alice, let's meet at 2pm'"

# Verbose logging
python main.py --verbose "send email to team about project update"

# Headless mode
python main.py --headless "send email to bob about schedule"

# Custom timeout
python main.py --timeout 60000 "send email to client about proposal"

# Show examples
python main.py --examples
```

### API Endpoint

```bash
# Start the API server
python api.py

# Send POST request to /execute
curl -X POST "http://localhost:8000/execute" \
     -H "Content-Type: application/json" \
     -d '{"instruction": "send email to test@example.com about demo saying hello"}'
```

## 🔧 Core Components

### 1. UniversalWebAgent
The main orchestrator that coordinates task execution across providers.

### 2. TaskParser
Converts natural language instructions into structured task information using LLM reasoning.

### 3. UIAnalyzer
Analyzes web page structure to identify interactive elements and their purposes.

### 4. BrowserController
Manages browser lifecycle and provides high-level automation methods.

### 5. Providers
Service-specific implementations (Gmail, Outlook) that handle authentication and task execution.

## 📁 Project Structure

```
task2/
├── core/
│   ├── __init__.py
│   ├── agent.py              # Main agent implementation
│   ├── browser_controller.py # Browser automation controller
│   ├── task_parser.py        # Natural language task parsing
│   ├── ui_analyzer.py        # UI analysis and element detection
│   ├── exceptions.py         # Custom exception classes
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base_provider.py  # Abstract provider interface
│   │   ├── gmail_provider.py # Gmail-specific implementation
│   │   └── outlook_provider.py # Outlook-specific implementation
│   └── mock_browser_controller.py # Mock browser for testing
├── main.py                   # CLI entry point
├── api.py                    # FastAPI endpoint
├── requirements.txt          # Python dependencies
├── .env.example             # Environment variables template
├── .gitignore               # Git ignore rules
└── README.md                # This file
```

## 🧪 Testing

### Test Browser Controller
```bash
python -c "import asyncio; from core.browser_controller import BrowserController; print('✅ Import successful')"
```

### Test Full System
```bash
# Set your OpenAI API key first
export OPENAI_API_KEY="your_key_here"

# Test with mock browser (no real browser needed)
python main.py "send email to test@example.com about test saying 'This is a test'"
```

## 🐛 Troubleshooting

### Common Issues

1. **Playwright Installation**:
   ```bash
   playwright install
   playwright install-deps
   ```

2. **Import Errors**: Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

3. **Browser Launch Issues**: Check if Playwright browsers are installed:
   ```bash
   playwright --version
   ```

4. **Credential Errors**: Verify your `.env` file has the correct credentials.

### Debug Mode

Enable verbose logging to see detailed execution steps:
```bash
python main.py --verbose "your instruction here"
```

## 🔮 Future Enhancements

- [ ] Support for more web services (Google Drive, Dropbox, etc.)
- [ ] Advanced error recovery and retry mechanisms
- [ ] Screenshot-based UI analysis
- [ ] Multi-language support
- [ ] Scheduled task execution
- [ ] Webhook integrations
- [ ] Performance monitoring and metrics

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## ⚠️ Disclaimer

This tool is for educational and development purposes. Always respect websites' terms of service and robots.txt files. Use responsibly and ethically.
