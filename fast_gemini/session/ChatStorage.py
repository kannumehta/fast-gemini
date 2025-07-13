from abc import ABC, abstractmethod
from typing import List
from pydantic import BaseModel
from .ChatMessage import ChatMessage, Role

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

    async def copy_model_response(self, from_chat_id: str, to_chat_id: str) -> None:
        """Copy MODEL role messages from one chat to another.
        
        Args:
            from_chat_id: The source chat ID to copy MODEL messages from
            to_chat_id: The target chat ID to append MODEL messages to
        """
        messages = await self.get_history(from_chat_id)
        model_messages = [msg for msg in messages if msg.role == Role.MODEL]
        await self.append_history(to_chat_id, model_messages)
