from typing import Dict, Any
from pydantic import BaseModel
from .Tool import Tool

class FunctionCall(BaseModel):
    tool: Tool
    function_call: Any

    def __init__(self, tool: Tool, function_call: Any):
        super().__init__(tool=tool, function_call=function_call)

    def __str__(self):
        return f"FunctionCall(tool={self.tool}, function_call={self.function_call})"

    def __repr__(self):
        return self.__str__()
