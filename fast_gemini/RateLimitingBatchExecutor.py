from typing import List, TypeVar
from .ToolExecutor import ToolExecutor
from .BatchToolExecutor import BatchToolExecutor
from .FunctionCall import FunctionCall
from .ToolsExecutionResult import ToolsExecutionResult

T = TypeVar('T')

class RateLimitingBatchExecutor(ToolExecutor[T]):
    def __init__(self, max_batch_size: int):
        """Initialize the rate limiting batch executor.
        
        Args:
            max_batch_size: Maximum number of tools to execute in a single batch
        """
        super().__init__()
        self.max_batch_size = max_batch_size
        self.batch_executor = BatchToolExecutor[T]()

    async def execute_tools(self, function_calls: List[FunctionCall]) -> ToolsExecutionResult:
        """Execute tools in batches of max_batch_size.
        
        Args:
            function_calls: List of FunctionCall objects to execute
            
        Returns:
            ToolsExecutionResult: Result containing the execution results and whether to proceed
        """
        all_results = []
        
        # Process function calls in batches
        for i in range(0, len(function_calls), self.max_batch_size):
            batch = function_calls[i:i + self.max_batch_size]
            batch_result = await self.batch_executor.execute_tools(batch)
            all_results.extend(batch_result.function_call_results)
            
        return ToolsExecutionResult(
            should_proceed=True,
            function_call_results=all_results
        ) 