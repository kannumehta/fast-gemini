from abc import ABC, abstractmethod
from typing import List
from .FunctionCall import FunctionCall
from .ToolsExecutionResult import ToolsExecutionResult
from pydantic import BaseModel

class ToolExecutor(BaseModel, ABC):
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
