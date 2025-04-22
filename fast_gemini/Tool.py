from abc import ABC, abstractmethod
from typing import Dict
from pydantic import BaseModel

class Tool(BaseModel, ABC):
    name: str
    function_definition: Dict

    def __init__(self, name: str, function_definition: Dict):
        super().__init__(name=name, function_definition=function_definition)

    def __str__(self):
        return f"Tool(name={self.name}, function_definition={self.function_definition})"

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    async def execute(self, tool_args: Dict) -> Dict:
        """
        Execute the tool with the provided arguments.
        
        Args:
            tool_args: Dictionary of arguments to pass to the tool
            
        Returns:
            Dict: The result of the tool execution
        """
        pass