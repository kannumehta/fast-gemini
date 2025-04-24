# Gemini Integration

A powerful Python library for interacting with Google's Gemini API, providing advanced features like tool execution, session management, and context caching.

## Features

- Asynchronous operation support
- Tool execution with concurrent processing
- Generic event streaming with type safety
- Streaming responses
- Error handling and retries
- Configurable tool execution modes
- Support for multiple tools
- Type hints and validation
- Session management with flexible storage backends
- Context caching with automatic TTL refresh
- Support for multiple storage implementations
- Easy integration with various databases

```bash
# Clone the repository
git clone https://github.com/kannumehta/fast-gemini.git
cd gemini

# Install in development mode
pip install -e .
```

Or install directly from the repository:

```bash
pip install git+https://github.com/kannumehta/fast-gemini.git
```

## Core Components

### GeminiClient

The main client for interacting with the Gemini API. It handles message processing, tool execution, and response streaming.

```python
from fast_gemini import GeminiClient, ChatManager, LocalChatStorage
from pydantic import BaseModel

# Initialize the client with a chat manager
chat_manager = ChatManager(storage=LocalChatStorage())
client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)

# Basic chat with tools
async for response in client.chat(
    query="What's the weather in New York?",
    model="gemini-pro",
    tools=[weather_tool],
    tool_executor=tool_executor
):
    print(response)
```

### Tool

Base class for creating custom tools that can be used with Gemini. Tools must implement the `execute` method.

```python
from fast_gemini import Tool
from typing import Dict
from pydantic import BaseModel

class SimpleTool(Tool):
    name: str = "simple_tool"
    function_definition: Dict = {
        "name": "simple_tool",
        "description": "A simple tool example",
        "parameters": {
            "type": "object",
            "properties": {
                "input": {
                    "type": "string",
                    "description": "Input parameter"
                }
            },
            "required": ["input"]
        }
    }

    async def execute(self, tool_args: Dict) -> Dict:
        # Your tool logic here
        return {"result": f"Processed: {tool_args['input']}"}
```

### ToolExecutor

Abstract base class for executing tools. Implement this to define how tools should be executed. The ToolExecutor supports generic event streaming, allowing you to emit typed events during tool execution.

```python
from fast_gemini import ToolExecutor, FunctionCall, ToolsExecutionResult
from typing import List, TypeVar, Generic
from pydantic import BaseModel

# Define your event type
class ToolEvent(BaseModel):
    type: str
    message: str
    data: dict

# Create a generic ToolExecutor with your event type
class CustomToolExecutor(ToolExecutor[ToolEvent]):
    async def execute_tools(self, function_calls: List[FunctionCall]) -> ToolsExecutionResult:
        # Emit a progress event
        await self._emit_event(ToolEvent(
            type="progress",
            message="Starting tool execution",
            data={"total_tools": len(function_calls)}
        ))
        
        results = []
        for i, call in enumerate(function_calls):
            # Emit progress for each tool
            await self._emit_event(ToolEvent(
                type="progress",
                message=f"Executing tool {i+1}/{len(function_calls)}",
                data={"tool_name": call.tool.name}
            ))
            
            # Execute the tool
            result = await call.tool.execute(call.function_call.args)
            results.append(result)
            
            # Emit result event
            await self._emit_event(ToolEvent(
                type="result",
                message=f"Tool {call.tool.name} completed",
                data={"result": result}
            ))
        
        return ToolsExecutionResult(should_proceed=True, function_call_results=results)
```

### Event Streaming

The ToolExecutor provides a powerful event streaming system that allows you to:
- Emit typed events during tool execution
- Stream progress updates, results, and errors
- Handle events in a type-safe manner
- Process events asynchronously

Here's how to use the event streaming in your application:

```python
from fast_gemini import ToolExecutor, FunctionCall, ToolsExecutionResult
from typing import List
from pydantic import BaseModel

# Define your event type
class ToolEvent(BaseModel):
    type: str
    message: str
    data: dict

async def main():
    # Initialize the executor with your event type
    executor = CustomToolExecutor()
    
    try:
        # Start tool execution
        result = await executor.execute_tools(function_calls)
        
        # Get the event stream
        stream = executor.get_result_stream()
        
        # Process events as they arrive
        async for event in stream:
            if event.type == "progress":
                print(f"Progress: {event.message}")
                # Update UI or log progress
            elif event.type == "result":
                print(f"Result: {event.message}")
                # Process tool results
                
    finally:
        # Clean up resources
        await executor.shutdown()
```

### AsyncToolExecutor

A concrete implementation of ToolExecutor that executes multiple tools concurrently using asyncio.

```python
from fast_gemini import AsyncToolExecutor
from pydantic import BaseModel

# Initialize the async executor with your event type
executor = AsyncToolExecutor[ToolEvent]()

# Use with GeminiClient
client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)
async for response in client.chat(
    query="What's the weather in multiple cities?",
    model="gemini-pro",
    tools=[weather_tool],
    tool_executor=executor
):
    print(response)
```

### RateLimitingAsyncExecutor

A ToolExecutor that limits the number of concurrent tool executions by processing them in batches.

```python
from fast_gemini import RateLimitingAsyncExecutor
from pydantic import BaseModel

# Initialize with max batch size of 5 and your event type
executor = RateLimitingAsyncExecutor[ToolEvent](max_batch_size=5)

# Use with GeminiClient
client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)
async for response in client.chat(
    query="Process multiple items",
    model="gemini-pro",
    tools=[processing_tool],
    tool_executor=executor
):
    print(response)
```

### Session Management

FastGemini provides robust session management through the `ChatManager` and `ChatStorage` components:

#### ChatManager

Manages the conversation state and handles message generation requests:

```python
from fast_gemini import ChatManager, LocalChatStorage
from pydantic import BaseModel

# Initialize with a storage backend
chat_manager = ChatManager(storage=LocalChatStorage())

# Generate a content request
generation_request = await chat_manager.generate_content_request(
    chat_id="1",
    query="What's the weather?",
    model="gemini-pro",
    client=client,
    tools=tools,
    tool_mode="any",
    cache_config=cache_config
)
```

#### ChatStorage

Abstract base class for implementing different storage backends. You can create custom storage implementations for various databases:

```python
from fast_gemini import ChatStorage, ChatMessage
from typing import List, Any
from pydantic import BaseModel

class RedisChatStorage(ChatStorage):
    redis_client: Any  # Type hint for Redis client

    def __init__(self, redis_client: Any):
        super().__init__(redis_client=redis_client)

    async def get_history(self, chat_id: str) -> List[ChatMessage]:
        # Implement Redis-specific storage logic
        pass

    async def update_history(self, chat_id: str, messages: List[ChatMessage]) -> None:
        # Implement Redis-specific update logic
        pass

    async def append_history(self, chat_id: str, messages: List[ChatMessage]) -> None:
        # Implement Redis-specific append logic
        pass

# Example usage with Redis
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
chat_manager = ChatManager(storage=RedisChatStorage(redis_client=redis_client))
```

### Context Caching

FastGemini includes a powerful caching system to improve performance and reduce costs:

#### CacheManager

Manages the creation, updating, and deletion of cached content:

```python
from fast_gemini import CacheManager, CacheConfig
from pydantic import BaseModel

# Initialize cache manager
cache_manager = CacheManager()

# Create a new cache
cache_name = await cache_manager.create_cache(
    client=client,
    model="gemini-pro",
    content="You are a helpful assistant.",
    ttl="1h",
    cache_name="my_cache"
)

# Update cache TTL
await cache_manager.update_cache_ttl(client, cache_name, "2h")

# Get and refresh cache
refreshed_cache = await cache_manager.get_and_refresh(client, cache_name, "1h")
```

#### CacheConfig

Configure caching behavior for your chat sessions:

```python
from fast_gemini import CacheConfig
from pydantic import BaseModel

# Basic cache configuration
cache_config = CacheConfig(
    cache_name="my_cache",
    auto_refresh_ttl="1h"  # Automatically refresh TTL on each use
)

# Use with chat
async for response in client.chat(
    query="What's the weather?",
    model="gemini-pro",
    tools=[weather_tool],
    tool_executor=tool_executor,
    cache_config=cache_config
):
    print(response)
```

### Storage Implementations

FastGemini supports various storage backends through the `ChatStorage` interface:

#### LocalChatStorage

Simple in-memory storage for development and testing:

```python
from fast_gemini import LocalChatStorage
from pydantic import BaseModel

chat_manager = ChatManager(storage=LocalChatStorage())
```

#### Database-backed Storage

Example implementations for different databases:

```python
# PostgreSQL Storage
class PostgresChatStorage(ChatStorage):
    connection_string: str

    def __init__(self, connection_string: str):
        super().__init__(connection_string=connection_string)
        self.conn = psycopg2.connect(connection_string)

    async def get_history(self, chat_id: str) -> List[ChatMessage]:
        # Implement PostgreSQL-specific storage logic
        pass

# MongoDB Storage
class MongoChatStorage(ChatStorage):
    mongo_client: Any  # Type hint for MongoDB client

    def __init__(self, mongo_client: Any):
        super().__init__(mongo_client=mongo_client)
        self.db = mongo_client.chat_db

    async def get_history(self, chat_id: str) -> List[ChatMessage]:
        # Implement MongoDB-specific storage logic
        pass

# Combined Storage
class HybridChatStorage(ChatStorage):
    redis_client: Any  # Type hint for Redis client
    mongo_client: Any  # Type hint for MongoDB client

    def __init__(self, redis_client: Any, mongo_client: Any):
        super().__init__(redis_client=redis_client, mongo_client=mongo_client)
        self.redis = redis_client
        self.mongo = mongo_client

    async def get_history(self, chat_id: str) -> List[ChatMessage]:
        # Implement hybrid storage logic
        pass
```

### Complete Example with All Features

Here's a complete example showing how to use all FastGemini features together:

```python
import asyncio
from fast_gemini import (
    GeminiClient, ChatManager, LocalChatStorage,
    AsyncToolExecutor, CacheConfig, Tool
)
from typing import Dict, Any
from pydantic import BaseModel

# Define a custom tool
class WeatherTool(Tool):
    name: str = "get_weather"
    function_definition: Dict = {
        "name": "get_weather",
        "description": "Get weather information for a location",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "The location to get weather for"
                }
            },
            "required": ["location"]
        }
    }

    async def execute(self, tool_args: Dict) -> Dict:
        location = tool_args["location"]
        # Implement weather API call here
        return {"temperature": "72°F", "condition": "Sunny"}

async def main():
    # Initialize components
    chat_manager = ChatManager(storage=LocalChatStorage())
    client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)
    weather_tool = WeatherTool()
    executor = AsyncToolExecutor[ToolEvent]()

    # Configure caching
    cache_config = CacheConfig(
        cache_name="weather_chat",
        auto_refresh_ttl="1h"
    )

    # Use the client with all features
    async for response in client.chat(
        query="What's the weather in New York?",
        model="gemini-pro",
        tools=[weather_tool],
        tool_executor=executor,
        cache_config=cache_config
    ):
        print(response)

if __name__ == "__main__":
    asyncio.run(main())
```

## Error Handling

The package includes several custom exceptions:

- `GeminiAPIError`: Raised when the Gemini API call fails
- `GeminiResponseError`: Raised when the response is invalid or empty
- `GeminiToolExecutionError`: Raised when tool execution fails
- `GeminiClientError`: Base exception for all Gemini client errors

## Configuration

The GeminiClient supports various configuration options:

- `tool_mode`: Controls how the model interacts with tools
  - `"any"`: The model can choose to use tools or not (default when tools are provided)
  - `"auto"`: The model will automatically use tools when appropriate
    - Automatically set when no tools are provided
    - Useful for basic chat interactions without tool execution
- `max_iterations`: Maximum number of iterations to prevent infinite loops
- `num_gemini_call_retries`: Number of retries for failed API calls

### Tool Modes and Usage Examples

#### Basic Chat (No Tools)
```python
client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)
async for response in client.chat(
    query="Tell me a story",
    model="gemini-pro",
    tools=[],  # No tools provided, tool_mode will be "auto"
    tool_executor=tool_executor
):
    print(response)
```

#### Chat with Tools (Any Mode)
```python
client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)
async for response in client.chat(
    query="What's the weather in New York?",
    model="gemini-pro",
    tools=[weather_tool],  # Tools provided, tool_mode defaults to "any"
    tool_executor=tool_executor
):
    print(response)
```

#### Chat with Tools (Auto Mode)
```python
client = GeminiClient(api_key="your-api-key", chat_manager=chat_manager)
async for response in client.chat(
    query="What's the weather in New York?",
    model="gemini-pro",
    tools=[weather_tool],
    tool_executor=tool_executor,
    tool_mode="auto"  # Explicitly set to auto mode
):
    print(response)
```

### Tool Mode Behavior

- When no tools are provided:
  - `tool_mode` is automatically set to "auto"
  - The model will not attempt to use any tools
  - Best for simple chat interactions

- When tools are provided:
  - `tool_mode` defaults to "any"
  - The model can choose whether to use tools
  - Can be explicitly set to "auto" to force tool usage
  - Best for complex interactions requiring tool execution

## Best Practices

1. Always implement proper error handling in tool execution
2. Use async/await for better performance
3. Implement proper validation in tool parameters
4. Use type hints for better code maintainability
5. Consider implementing rate limiting for API calls
6. Cache tool results when appropriate
7. Implement proper logging for debugging
8. Use typed events for better type safety and IDE support
9. Always call shutdown() to clean up resources
10. Handle events asynchronously to avoid blocking

## Context Caching

We've implemented context caching to improve performance and reduce costs. This feature allows you to:

- Cache input tokens for repeated use
- Reduce costs for frequently used prompts
- Improve response times for similar queries
- Set custom TTL (Time To Live) for cached content
- Automatically refresh cache TTL when needed

### Cache Configuration

The caching system is highly configurable through the `CacheConfig` class:

```python
from fast_gemini import CacheConfig

# Basic cache usage
cache_config = CacheConfig(
    cache_name="my_cache",
    auto_refresh_ttl=None  # No automatic refresh
)

# Cache with automatic TTL refresh
cache_config = CacheConfig(
    cache_name="my_cache",
    auto_refresh_ttl="1h"  # Refresh TTL to 1 hour on each use
)
```

### Cache Management

The `CacheManager` provides a complete interface for cache operations:

```python
from fast_gemini import GeminiClient, CacheManager

# Initialize client and cache manager
client = GeminiClient(api_key="your-api-key")
cache_manager = client.cache_manager

# Create a new cache
cache_name = cache_manager.create_cache(
    model="gemini-pro",
    content="You are a helpful assistant.",
    ttl="1h",
    cache_name="my_cache"  # Optional custom name
)

# List all caches
caches = cache_manager.list_caches()

# Get cache details
cache = cache_manager.get_cache(cache_name)

# Update cache TTL
cache_manager.update_cache_ttl(cache_name, "2h")

# Delete a cache
cache_manager.delete_cache(cache_name)
```

### Using Cached Content

You can use cached content in your chat requests:

```python
# Basic chat with cached content
async for response in client.chat(
    query="What's the weather?",
    model="gemini-pro",
    tools=[weather_tool],
    tool_executor=tool_executor,
    cache_config=CacheConfig(
        cache_name="weather_cache",
        auto_refresh_ttl="1h"
    )
):
    print(response)
```

### Use Cases

1. **Chatbots with System Instructions**
   - Cache your system instructions to reduce token costs
   - Automatically refresh TTL to keep instructions active

2. **Document Analysis**
   - Cache large documents for repeated analysis
   - Use different caches for different document types

3. **Code Repository Analysis**
   - Cache repository context for multiple queries
   - Refresh TTL based on repository update frequency

4. **Video Analysis**
   - Cache video content for multiple analysis requests
   - Use longer TTL for frequently accessed videos

### Best Practices

1. **Cache Naming**
   - Use descriptive names for your caches
   - Include model and content type in the name
   - Example: `weather_gemini_pro_cache`

2. **TTL Management**
   - Set appropriate TTL based on content update frequency
   - Use auto_refresh_ttl for frequently accessed caches
   - Consider content expiration needs

3. **Cache Cleanup**
   - Regularly clean up unused caches
   - Monitor cache usage and adjust TTL accordingly
   - Implement cache rotation for large applications

4. **Error Handling**
   - Always verify cache existence before use
   - Handle cache creation/deletion errors gracefully
   - Implement fallback for cache failures

For more details, see the [Gemini API Caching Documentation](https://ai.google.dev/gemini-api/docs/caching?lang=python). 