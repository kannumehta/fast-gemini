import asyncio
from typing import Dict, List, Optional, Any, AsyncGenerator
from google import genai
from google.genai import types, errors

from .Tool import Tool
from .ToolExecutor import ToolExecutor
from .ToolsExecutionResult import ToolsExecutionResult
from .FunctionCall import FunctionCall
from .exceptions import GeminiAPIError, GeminiResponseError, GeminiToolExecutionError, GeminiClientError
from .CacheConfig import CacheConfig
from .session.ChatManager import ChatManager
from .session.ChatMessage import ChatMessage
from .session.GenerateContentRequest import GenerateContentRequest
from .utils.logger import get_logger

logger = get_logger()

class GeminiClient:
    def __init__(self, api_key: str, chat_manager: ChatManager):
        """Initialize the Gemini client with an API key.
        
        Args:
            api_key: The Gemini API key
        """
        logger.info("Initializing GeminiClient")
        self.client = genai.Client(api_key=api_key)
        self.chat_manager = chat_manager

    async def _get_gemini_response(self, model: str, generation_request: GenerateContentRequest) -> Optional[Any]:
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
        logger.debug(f"Getting Gemini response for model: {model}")
        try:
            response = await self.client.aio.models.generate_content(
                model=model,
                contents=[c.to_content() for c in generation_request.contents],
                config=generation_request.config
            )

            if not response or not response.candidates:
                logger.error("No response generated from Gemini")
                raise GeminiResponseError("No response generated")

            candidate = response.candidates[0]
            if not candidate.content or not candidate.content.parts:
                logger.error("Empty response content from Gemini")
                raise GeminiResponseError("Empty response content")

            logger.debug("Successfully received Gemini response")
            return response

        except errors.APIError as e:
            logger.error(f"Gemini API error: {e.code} - {e.message}")
            raise GeminiAPIError(e.code, e.message)
        except Exception as e:
            logger.error(f"Unexpected error in Gemini API call: {str(e)}")
            raise GeminiAPIError("UNKNOWN", str(e))

    async def _get_gemini_response_with_retry(self, model: str, generation_request: GenerateContentRequest, num_retries: int = 1) -> Optional[Any]:
        """Get response from Gemini API with retries on failure.

        Args:
            messages: List of messages to send to Gemini
            config: Configuration for the Gemini API call
            model: Model to use for the API call
            num_retries: Number of retries to attempt on failure (default: 1)

        Returns:
            Optional[Any]: Gemini response if successful, None if error occurred after retries
        """
        logger.info(f"Attempting Gemini API call with {num_retries} retries")
        for attempt in range(num_retries + 1):
            try:
                return await self._get_gemini_response(model, generation_request)
            except GeminiAPIError:
                if attempt < num_retries:
                    logger.warning(f"Retry attempt {attempt + 1} of {num_retries}")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                else:
                    logger.error("All retry attempts failed")
                    raise
        return None

    def _extract_text_parts(self, parts: List[Any]) -> List[str]:
        """Extract text parts from Gemini response parts.

        Args:
            parts: List of parts from Gemini response

        Returns:
            List[str]: List of text responses
        """
        logger.debug("Extracting text parts from response")
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
        logger.debug("Extracting function calls from response")
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
        logger.debug("Processing Gemini response")
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
        logger.debug("Creating tool calls from function calls")
        tool_calls = []
        for function_call, part in function_calls:
            tool = next((t for t in tools if t.name == function_call.name), None)
            if tool is None:
                logger.error(f"Tool {function_call.name} not found")
                raise GeminiToolExecutionError(f"Tool {function_call.name} not found")
            tool_calls.append(FunctionCall(
                tool=tool,
                function_call=function_call
            ))
        return tool_calls

    async def _update_generation_request(self, generation_request: GenerateContentRequest, execution_result: ToolsExecutionResult) -> None:
        """Update messages with function call results.
        
        Args:
            generation_request: Current generation request
            execution_result: Results from tool execution
        """
        logger.debug("Updating generation request with tool execution results")
        for result in execution_result.function_call_results:
            # Append the function call
            generation_request.contents.append(ChatMessage.from_function_call(
                tool_name=result.function_call.tool.name,
                tool_args=result.function_call.function_call.args
            ))
            generation_request.contents.append(ChatMessage.from_function_result(
                tool_name=result.function_call.tool.name,
                tool_result=result.result
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
        chat_id = "1"
        logger.info(f"Starting chat session with model: {model}, tool_mode: {tool_mode}")
        generation_request = await self.chat_manager.generate_content_request(
            chat_id=chat_id,
            query=query,
            model=model,
            client=self.client,
            tools=tools,
            tool_mode=tool_mode,
            cache_config=cache_config
        )

        # Process response and handle tool calls
        iteration = 0

        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Chat iteration {iteration}/{max_iterations}")

            # Get response from Gemini
            response = await self._get_gemini_response_with_retry(model, generation_request, num_gemini_call_retries)
            if response is None:
                logger.error("No response generated after retries")
                raise GeminiResponseError("No response generated")

            # Process response
            text_parts, function_calls = await self._process_response(response)

            # Yield all text parts first
            for text in text_parts:
                yield text

            if not function_calls:
                logger.debug("No function calls in response, ending chat session")
                break

            # Convert and execute tool calls
            tool_calls = await self._create_tool_calls(function_calls, tools)
            execution_result = await tool_executor.execute_tools(tool_calls)

            # Update messages with results
            await self._update_generation_request(generation_request, execution_result)

            if not execution_result.should_proceed:
                await self.chat_manager.chat_storage.update_history(chat_id, generation_request.contents)
                logger.debug("Tool execution indicates should not proceed, ending chat session")
                break

        if iteration >= max_iterations:
            logger.warning("Maximum tool iterations reached")
            yield "Maximum tool iterations reached."
