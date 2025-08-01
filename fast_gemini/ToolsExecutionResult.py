from typing import List
from pydantic import BaseModel
from .FunctionCallResult import FunctionCallResult

class ToolsExecutionResult(BaseModel):
    should_proceed: bool
    function_call_results: List[FunctionCallResult]

    def __init__(self, should_proceed: bool, function_call_results: List[FunctionCallResult]):
        super().__init__(should_proceed=should_proceed, function_call_results=function_call_results)

    def __str__(self):
        return f"ToolsExecutionResult(should_proceed={self.should_proceed}, function_call_results={self.function_call_results})"

    def __repr__(self):
        return self.__str__()
