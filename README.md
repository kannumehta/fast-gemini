# Gemini Integration

This package provides a Python integration with Google's Gemini API, allowing for advanced AI interactions with tool execution capabilities. The integration supports asynchronous operations, tool execution, and streaming responses.

## Installation

You can install the package locally using pip:

```bash
# Clone the repository
git clone https://github.com/yourusername/gemini.git
cd gemini

# Install in development mode
pip install -e .
```

Or install directly from the repository:

```bash
pip install git+https://github.com/yourusername/gemini.git
```

## Core Components

### GeminiClient

The main client for interacting with the Gemini API. It handles message processing, tool execution, and response streaming.

```python
from fast_gemini import GeminiClient

# Initialize the client
client = GeminiClient(api_key="your-api-key")

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

### BatchToolExecutor

A concrete implementation of ToolExecutor that executes multiple tools concurrently using asyncio.

```python
from fast_gemini import BatchToolExecutor

# Initialize the batch executor with your event type
executor = BatchToolExecutor[ToolEvent]()

# Use with GeminiClient
client = GeminiClient(api_key="your-api-key")
async for response in client.chat(
    query="What's the weather in multiple cities?",
    model="gemini-pro",
    tools=[weather_tool],
    tool_executor=executor
):
    print(response)
```

### RateLimitingBatchExecutor

A ToolExecutor that limits the number of concurrent tool executions by processing them in batches.

```python
from fast_gemini import RateLimitingBatchExecutor

# Initialize with max batch size of 5 and your event type
executor = RateLimitingBatchExecutor[ToolEvent](max_batch_size=5)

# Use with GeminiClient
client = GeminiClient(api_key="your-api-key")
async for response in client.chat(
    query="Process multiple items",
    model="gemini-pro",
    tools=[processing_tool],
    tool_executor=executor
):
    print(response)
```

## Complete Example

Here's a complete example showing how to use the Gemini integration with custom tools and event streaming:

```python
import asyncio
from fast_gemini import GeminiClient, Tool, BatchToolExecutor
from typing import Dict
from pydantic import BaseModel

# Define your event type
class ToolEvent(BaseModel):
    type: str
    message: str
    data: dict

# Define a custom tool
class CalculatorTool(Tool):
    name: str = "calculate"
    function_definition: Dict = {
        "name": "calculate",
        "description": "Perform mathematical calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    }

    async def execute(self, tool_args: Dict) -> Dict:
        expression = tool_args["expression"]
        try:
            result = eval(expression)
            return {"result": result}
        except Exception as e:
            return {"error": str(e)}

# Custom executor with event streaming
class StreamingCalculatorExecutor(BatchToolExecutor[ToolEvent]):
    async def execute_tools(self, function_calls: List[FunctionCall]) -> ToolsExecutionResult:
        # Emit start event
        await self._emit_event(ToolEvent(
            type="start",
            message="Starting calculations",
            data={"total": len(function_calls)}
        ))
        
        # Execute tools
        results = await super().execute_tools(function_calls)
        
        # Emit completion event
        await self._emit_event(ToolEvent(
            type="complete",
            message="All calculations completed",
            data={"results": results.function_call_results}
        ))
        
        return results

async def main():
    # Initialize components
    client = GeminiClient(api_key="your-api-key")
    calculator_tool = CalculatorTool()
    executor = StreamingCalculatorExecutor()

    # Use the client with event streaming
    async for response in client.chat(
        query="Calculate 2 + 2 and 3 * 3",
        model="gemini-pro",
        tools=[calculator_tool],
        tool_executor=executor
    ):
        print(response)
        
    # Process events
    stream = executor.get_result_stream()
    async for event in stream:
        if event.type == "start":
            print(f"Starting {event.data['total']} calculations")
        elif event.type == "complete":
            print("All calculations completed")
            for result in event.data["results"]:
                print(f"Result: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

## Features

- Asynchronous operation support
- Tool execution with concurrent processing
- Generic event streaming with type safety
- Streaming responses
- Error handling and retries
- Configurable tool execution modes
- Support for multiple tools
- Type hints and validation

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
client = GeminiClient(api_key="your-api-key")
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
client = GeminiClient(api_key="your-api-key")
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
client = GeminiClient(api_key="your-api-key")
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