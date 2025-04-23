import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from google import genai
from google.genai import types, errors

from .Tool import Tool
from .ToolExecutor import ToolExecutor
from .ToolsExecutionResult import ToolsExecutionResult
from .FunctionCall import FunctionCall
from .exceptions import GeminiAPIError, GeminiResponseError, GeminiToolExecutionError, GeminiClientError
from .CacheManager import CacheManager
from .CacheConfig import CacheConfig

class GeminiClient:
    def __init__(self, api_key: str):
        """Initialize the Gemini client with an API key.
        
        Args:
            api_key: The Gemini API key
        """
        self.client = genai.Client(api_key=api_key)
        self.default_config = {
            "automatic_function_calling": {"disable": True},
            "tool_config": {"function_calling_config": {"mode": "any"}},
        }
        self.cache_manager = CacheManager(self.client)

    def _get_config_with_tools(self, tools: List[Tool], tool_mode: str = "any", cache_config: Optional[CacheConfig] = None) -> Dict:
        """Get configuration with tools added.
        
        Args:
            tools: List of tools to add to configuration
            tool_mode: Mode for tool calling - "any" or "auto" (default: "any")
            cache_config: Optional cache configuration
            
        Returns:
            Dict: Configuration with tools added
        """
        config = self.default_config.copy()
        if cache_config:
            config["cached_content"] = cache_config.cache_name
        
        # If no tools are provided, force tool_mode to "auto"
        if not tools:
            tool_mode = "auto"
            config["tool_config"] = {"function_calling_config": {"mode": tool_mode}}
            
            return config
            
        config["tools"] = [types.Tool(function_declarations=[tool.function_definition for tool in tools])]
        config["tool_config"] = {"function_calling_config": {"mode": tool_mode}}
        
        return config

    async def _get_gemini_response(self, messages: List[Dict], config: Dict, model: str) -> Optional[Any]:
        """Get response from Gemini API with error handling.

        Args:
            messages: List of messages to send to Gemini
            config: Configuration for the Gemini API call
            model: Model to use for the API call

        Returns:
            Optional[Any]: Gemini response if successful, None if error occurred

        Raises:
            GeminiAPIError: If the API call fails
            GeminiResponseError: If the response is invalid or empty
        """
        try:
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=messages,
                config=config
            )

            if not response or not response.candidates:
                raise GeminiResponseError("No response generated")

            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                raise GeminiResponseError("Empty response content")

            return response

        except errors.APIError as e:
            raise GeminiAPIError(e.code, e.message)
        except Exception as e:
            raise GeminiAPIError("UNKNOWN", str(e))

    async def _get_gemini_response_with_retry(self, messages: List[Dict], config: Dict, model: str, num_retries: int = 1) -> Optional[Any]:
        """Get response from Gemini API with retries on failure.

        Args:
            messages: List of messages to send to Gemini
            config: Configuration for the Gemini API call
            model: Model to use for the API call
            num_retries: Number of retries to attempt on failure (default: 1)

        Returns:
            Optional[Any]: Gemini response if successful, None if error occurred after retries
        """
        for attempt in range(num_retries + 1):
            try:
                return await self._get_gemini_response(messages, config, model)
            except GeminiAPIError:
                if attempt < num_retries:
                    await asyncio.sleep(1)  # Wait 1 second before retry
                else:
                    raise
        return None

    def _extract_text_parts(self, parts: List[Any]) -> List[str]:
        """Extract text parts from Gemini response parts.

        Args:
            parts: List of parts from Gemini response

        Returns:
            List[str]: List of text responses
        """
        text_parts = []
        for part in parts:
            if hasattr(part, 'text') and part.text:
                text_parts.append(part.text)
        return text_parts

    def _extract_function_calls(self, parts: List[Any]) -> List[tuple]:
        """Extract function calls from Gemini response parts.

        Args:
            parts: List of parts from Gemini response

        Returns:
            List[tuple]: List of tuples containing (function_call, part)
        """
        function_calls = []
        for part in parts:
            if hasattr(part, 'function_call') and part.function_call:
                function_call = part.function_call
                if not function_call.name:
                    continue
                function_calls.append((function_call, part))
        return function_calls

    async def _process_response(self, response: Any) -> tuple[List[str], List[tuple]]:
        """Process a Gemini response to extract text parts and function calls.
        
        Args:
            response: The Gemini API response
            
        Returns:
            tuple[List[str], List[tuple]]: Text parts and function calls
        """
        text_parts = self._extract_text_parts(response.candidates[0].content.parts)
        function_calls = self._extract_function_calls(response.candidates[0].content.parts)
        return text_parts, function_calls

    async def _create_tool_calls(self, function_calls: List[tuple], tools: List[Tool]) -> List[FunctionCall]:
        """Convert raw function calls to FunctionCall objects.
        
        Args:
            function_calls: List of raw function calls
            tools: List of available tools
            
        Returns:
            List[FunctionCall]: List of properly constructed FunctionCall objects
            
        Raises:
            GeminiToolExecutionError: If a tool is not found
        """
        tool_calls = []
        for function_call, part in function_calls:
            tool = next((t for t in tools if t.name == function_call.name), None)
            if tool is None:
                raise GeminiToolExecutionError(f"Tool {function_call.name} not found")
            tool_calls.append(FunctionCall(
                tool=tool,
                function_call=function_call
            ))
        return tool_calls

    async def _update_messages(self, messages: List[Dict], execution_result: ToolsExecutionResult) -> None:
        """Update messages with function call results.
        
        Args:
            messages: Current message history
            execution_result: Results from tool execution
        """
        for result in execution_result.function_call_results:
            # Append the function call
            messages.append(types.Content(
                role="model",
                parts=[types.Part(function_call=result.function_call.function_call)]
            ))
            messages.append(types.Content(
                role="user",
                parts=[types.Part.from_function_response(
                    name=result.function_call.tool.name,
                    response={"result": result.result}
                )]
            ))

    async def chat(
        self,
        query: str,
        model: str,
        tools: List[Tool],
        tool_executor: ToolExecutor,
        max_iterations: int = 10,
        num_gemini_call_retries: int = 1,
        tool_mode: str = "any",
        cache_config: Optional[CacheConfig] = None
    ) -> AsyncGenerator[str, None]:
        """Process a query using Gemini and available tools, streaming responses.

        Args:
            query: The user's query
            model: The model to use
            tools: List of available tools
            tool_executor: Executor for tool calls
            max_iterations: Maximum number of iterations to prevent infinite loops (default: 10)
            num_gemini_call_retries: Number of retries to attempt on Gemini API calls (default: 1)
            tool_mode: Mode for tool calling - "any" or "auto" (default: "any")
            cache_config: Optional cache configuration for using cached content

        Yields:
            str: Stream of text responses

        Raises:
            GeminiAPIError: If the API call fails
            GeminiResponseError: If the response is invalid or empty
            GeminiToolExecutionError: If tool execution fails
        """
        # Handle cache refresh if needed
        if cache_config:
            if cache_config.auto_refresh_ttl:
                # Refresh the cache with new TTL
                await self.cache_manager.get_and_refresh(cache_config.cache_name, cache_config.auto_refresh_ttl)
            else:
                # Just verify the cache exists
                await self.cache_manager.get_cache(cache_config.cache_name)

        # Get config with tools
        config = self._get_config_with_tools(tools, tool_mode, cache_config)

        # Initialize messages
        messages = [types.Content(role="user", parts=[types.Part(text=query)])]

        # Process response and handle tool calls
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Get response from Gemini
            response = await self._get_gemini_response_with_retry(messages, config, model, num_gemini_call_retries)
            if response is None:
                raise GeminiResponseError("No response generated")

            # Process response
            text_parts, function_calls = await self._process_response(response)

            # Yield all text parts first
            for text in text_parts:
                yield text

            if not function_calls:
                break

            # Convert and execute tool calls
            tool_calls = await self._create_tool_calls(function_calls, tools)
            execution_result = await tool_executor.execute_tools(tool_calls)
            
            if not execution_result.should_proceed:
                break

            # Update messages with results
            await self._update_messages(messages, execution_result)

        if iteration >= max_iterations:
            yield "\n[Warning: Maximum iterations reached. Stopping to prevent infinite loop.]"
