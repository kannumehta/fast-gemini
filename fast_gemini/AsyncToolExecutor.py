import asyncio
from typing import List, TypeVar, Dict, Any
from .ToolExecutor import ToolExecutor
from .FunctionCall import FunctionCall
from .FunctionCallResult import FunctionCallResult
from .ToolsExecutionResult import ToolsExecutionResult

T = TypeVar('T')

class AsyncToolExecutor(ToolExecutor[T]):
    async def execute_tools(self, function_calls: List[FunctionCall]) -> ToolsExecutionResult:
        """
        Execute multiple function calls concurrently using asyncio tasks.
        
        Args:
            function_calls: List of FunctionCall objects to execute
            
        Returns:
            ToolsExecutionResult: Result containing the execution results and whether to proceed
        """
        # Create tasks for each function call
        tasks = [
            function_call.tool.execute(function_call.function_call.args)
            for function_call in function_calls
        ]
        
        # Execute all tasks concurrently and gather results
        results = await asyncio.gather(*tasks)
        
        # Create FunctionCallResult objects
        function_call_results = [
            FunctionCallResult(function_call=function_call, result=result)
            for function_call, result in zip(function_calls, results)
        ]
        
        return ToolsExecutionResult(
            should_proceed=True,
            function_call_results=function_call_results
        )
