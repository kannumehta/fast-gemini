from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from .ChatMessage import ChatMessage

class ChatStorage(BaseModel, ABC):
    """Abstract base class for chat storage implementations.
    
    This class defines the interface for storing and retrieving chat messages.
    Concrete implementations must provide storage-specific logic for these operations.
    """
    
    @abstractmethod
    async def get_history(self, chat_id: str) -> List[ChatMessage]:
        """Retrieve the chat history for a given chat ID.
        
        Args:
            chat_id: The unique identifier for the chat session
            
        Returns:
            List[ChatMessage]: A list of chat messages in the conversation
        """
        pass
    
    @abstractmethod
    async def update_history(self, chat_id: str, messages: List[ChatMessage]) -> None:
        """Update the chat history for a given chat ID.
        
        Args:
            chat_id: The unique identifier for the chat session
            messages: The list of chat messages to store
        """
        pass

    @abstractmethod
    async def append_history(self, chat_id: str, messages: List[ChatMessage]) -> None:
        """Append new messages to the existing chat history for a given chat ID.
        
        Args:
            chat_id: The unique identifier for the chat session
            messages: The list of new chat messages to append to the existing history
        """
        pass
