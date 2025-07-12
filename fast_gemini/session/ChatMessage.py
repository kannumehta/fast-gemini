from enum import Enum
from typing import Dict, Union
from pydantic import BaseModel
from google.genai import types
from ..GeminiFile import GeminiFile

class Role(str, Enum):
    USER = "user"
    MODEL = "model"

class UserResponse(BaseModel):
    query: str

class FunctionCall(BaseModel):
    tool_name: str
    tool_args: Dict

class FunctionResult(BaseModel):
    tool_name: str
    tool_result: Dict

class FileContent(BaseModel):
    file: GeminiFile

class ChatMessage(BaseModel):
    role: Role
    content: Union[UserResponse, FunctionCall, FunctionResult, FileContent]

    def to_content(self) -> types.Content:
        """Convert ChatMessage to types.Content based on content type.
        
        Returns:
            types.Content: The converted content object
        """
        if isinstance(self.content, UserResponse):
            return types.Content(
                role=self.role.value,
                parts=[types.Part(text=self.content.query)]
            )
        elif isinstance(self.content, FunctionCall):
            return types.Content(
                role=self.role.value,
                parts=[types.Part(function_call=types.FunctionCall(
                    name=self.content.tool_name,
                    args=self.content.tool_args
                ))]
            )
        elif isinstance(self.content, FunctionResult):
            return types.Content(
                role=self.role.value,
                parts=[types.Part.from_function_response(
                    name=self.content.tool_name,
                    response={"result": self.content.tool_result}
                )]
            )
        elif isinstance(self.content, FileContent):
            return types.Content(
                role=self.role.value,
                parts=[types.Part.from_uri(
                    file_uri=self.content.file.uri,
                    mime_type=self.content.file.mime_type
                )]
            )
        else:
            raise ValueError(f"Unknown content type: {type(self.content)}")

    def to_json(self) -> Dict:
        """Convert ChatMessage to a JSON-serializable dictionary.
        
        Returns:
            Dict: A dictionary representation of the ChatMessage
        """
        content_dict = {
            "role": self.role.value,
            "content_type": self.content.__class__.__name__,
            "content": self.content.model_dump()
        }
        return content_dict

    @staticmethod
    def from_json(data: Dict) -> 'ChatMessage':
        """Create a ChatMessage instance from a JSON dictionary.
        
        Args:
            data: Dictionary containing the serialized ChatMessage data
            
        Returns:
            ChatMessage: A new ChatMessage instance
            
        Raises:
            ValueError: If the content type is unknown or data is invalid
        """
        if not isinstance(data, dict):
            raise ValueError("Input must be a dictionary")
            
        if "role" not in data or "content_type" not in data or "content" not in data:
            raise ValueError("Missing required fields in input data")
            
        role = Role(data["role"])
        content_type = data["content_type"]
        content_data = data["content"]
        
        if content_type == "UserResponse":
            content = UserResponse(**content_data)
        elif content_type == "FunctionCall":
            content = FunctionCall(**content_data)
        elif content_type == "FunctionResult":
            content = FunctionResult(**content_data)
        elif content_type == "FileContent":
            content = FileContent(**content_data)
        else:
            raise ValueError(f"Unknown content type: {content_type}")
            
        return ChatMessage(role=role, content=content)
    
    @staticmethod
    def from_user_query(query: str) -> 'ChatMessage':
        """Create a ChatMessage instance with a UserResponse content.
        
        Args:
            query: The user's query string
            
        Returns:
            ChatMessage: A new ChatMessage instance with UserResponse content
        """
        return ChatMessage(
            role=Role.USER,
            content=UserResponse(query=query)
        )

    @staticmethod
    def from_function_call(tool_name: str, tool_args: Dict) -> 'ChatMessage':
        """Create a ChatMessage instance with a FunctionCall content.
        
        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments for the tool call
            
        Returns:
            ChatMessage: A new ChatMessage instance with FunctionCall content
        """
        return ChatMessage(
            role=Role.MODEL,
            content=FunctionCall(tool_name=tool_name, tool_args=tool_args)
        )

    @staticmethod
    def from_function_result(tool_name: str, tool_result: Dict) -> 'ChatMessage':
        """Create a ChatMessage instance with a FunctionResult content.
        
        Args:
            tool_name: Name of the tool that produced the result
            tool_result: Result from the tool execution
            
        Returns:
            ChatMessage: A new ChatMessage instance with FunctionResult content
        """
        return ChatMessage(
            role=Role.MODEL,
            content=FunctionResult(tool_name=tool_name, tool_result=tool_result)
        )

    @staticmethod
    def from_file(file: GeminiFile) -> 'ChatMessage':
        """Create a ChatMessage instance with a FileContent.
        
        Args:
            file: The GeminiFile object containing uri and mime_type
            
        Returns:
            ChatMessage: A new ChatMessage instance with FileContent
        """
        return ChatMessage(
            role=Role.USER,
            content=FileContent(file=file)
        )
