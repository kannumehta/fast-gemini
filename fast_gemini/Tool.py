from abc import ABC, abstractmethod
from typing import Dict
from pydantic import BaseModel

class Tool(BaseModel, ABC):
    name: str
    function_definition: Dict

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