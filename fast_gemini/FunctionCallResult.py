from typing import Dict
from pydantic import BaseModel
from .FunctionCall import FunctionCall

class FunctionCallResult(BaseModel):
    function_call: FunctionCall
    result: Dict

    def __init__(self, function_call: FunctionCall, response: Dict):
        super().__init__(function_call=function_call, response=response)

    def __str__(self):
        return f"FunctionCallResult(function_call={self.function_call}, result={self.result})"

    def __repr__(self):
        return self.__str__() 