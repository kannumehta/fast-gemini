import asyncio
from typing import List, TypeVar, Dict, Any
from .ToolExecutor import ToolExecutor
from .FunctionCall import FunctionCall
from .FunctionCallResult import FunctionCallResult
from .ToolsExecutionResult import ToolsExecutionResult
from .utils.logger import debug

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
        debug("Starting execution of %d function calls", len(function_calls))
        
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
        
        # Log each function call and its result
        for function_call, result in zip(function_calls, results):
            debug("Function call details:")
            debug("  Name: %s", function_call.function_call.name)
            debug("  Args: %s", function_call.function_call.args)
            debug("  Tool: %s", function_call.tool)
            debug("  Result: %s", result)
        
        debug("Completed execution of all function calls")
        
        return ToolsExecutionResult(
            should_proceed=True,
            function_call_results=function_call_results
        )
