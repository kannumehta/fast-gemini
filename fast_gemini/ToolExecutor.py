from abc import ABC, abstractmethod
from typing import List, AsyncGenerator, Any, TypeVar, Generic
from .FunctionCall import FunctionCall
from .ToolsExecutionResult import ToolsExecutionResult
from pydantic import BaseModel
import asyncio
from asyncio import Queue

T = TypeVar('T')

class ToolExecutor(BaseModel, Generic[T], ABC):
    def model_post_init(self, __context: Any) -> None:
        super().model_post_init(__context)
        self._event_queue: Queue[T] = Queue()
        self._result_stream = self._create_stream()

    def _create_stream(self) -> AsyncGenerator[T, None]:
        async def stream():
            while True:
                event = await self._event_queue.get()
                if event is None:  # Signal to stop
                    break
                yield event
        return stream()

    async def _emit_event(self, event: T):
        """
        Emit an event to the result stream. This method is intended to be used by subclasses
        to send events to the stream during tool execution.
        
        Args:
            event: The event to emit to the stream
        """
        await self._event_queue.put(event)

    def get_result_stream(self) -> AsyncGenerator[T, None]:
        """
        Get the result stream for consuming events.
        
        Returns:
            AsyncGenerator[T, None]: The stream of events
        """
        return self._result_stream

    async def shutdown(self):
        """
        Clean up resources and stop the stream.
        This should be called when the executor is no longer needed.
        """
        # Signal the stream to stop
        await self._event_queue.put(None)
        # Clear the queue
        while not self._event_queue.empty():
            try:
                self._event_queue.get_nowait()
            except asyncio.QueueEmpty:
                break
        # Clear the stream reference
        self._result_stream = None

    @abstractmethod
    async def execute_tools(self, function_calls: List[FunctionCall]) -> ToolsExecutionResult:
        """
        Execute a list of function calls.
        
        Args:
            function_calls: List of FunctionCall objects to execute
            
        Returns:
            ToolsExecutionResult: Result containing the execution results and whether to proceed
        """
        pass
