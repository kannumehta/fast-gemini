# Fast Gemini

A high-performance Python client for the Gemini API with advanced features like caching, tool execution, and comprehensive logging.

## Logging System

The Fast Gemini client includes a comprehensive logging system that provides both console output and file-based logging. The logging system is designed to be configurable and easy to use.

### Log Levels

The logging system supports the following log levels (in order of increasing severity):
- DEBUG: Detailed information for debugging
- INFO: General information about program execution
- WARNING: Indicates a potential problem
- ERROR: A more serious problem
- CRITICAL: A critical problem that may prevent the program from running

### Configuration

The log level can be configured using the `FAST_GEMINI_LOG_LEVEL` environment variable. Valid values are:
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

Example:
```bash
export FAST_GEMINI_LOG_LEVEL=DEBUG
```

### Log Files

Logs are stored in the `logs` directory within the Fast Gemini package. The log file is named `fast_gemini.log` and uses a rotating file handler with the following configuration:
- Maximum file size: 10MB
- Number of backup files: 5

### Usage

To use the logger in your code:

```python
from fast_gemini.utils.logger import get_logger

logger = get_logger()

# Log messages
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

Or use the convenience functions:

```python
from fast_gemini.utils.logger import debug, info, warning, error, critical

debug("Debug message")
info("Info message")
warning("Warning message")
error("Error message")
critical("Critical message")
```

### Log Format

The log format includes:
- Timestamp
- Logger name
- Log level
- Message
- File name and line number (for file logs)

Example log entry:
```
2024-03-14 10:30:45,123 - fast_gemini - INFO - Starting chat session with model: gemini-pro
```

## Features

- Asynchronous API calls
- Tool execution support
- Caching system
- Comprehensive logging
- Error handling
- Retry mechanism

## Installation

```bash
pip install fast-gemini
```

## Usage

```python
from fast_gemini import GeminiClient, ChatManager, ChatStorage, CacheManager

# Initialize components
chat_storage = ChatStorage()
cache_manager = CacheManager()
chat_manager = ChatManager(
    system_prompt="You are a helpful assistant.",
    chat_storage=chat_storage,
    cache_manager=cache_manager
)

# Create client
client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)

# Use the client
async for response in client.chat(
    query="What is the weather?",
    model="gemini-pro",
    tools=[],  # Add your tools here
    tool_executor=None  # Add your tool executor here
):
    print(response)
``` 