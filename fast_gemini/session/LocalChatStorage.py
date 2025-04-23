from typing import Dict, List
import copy
from .ChatStorage import ChatStorage
from .ChatMessage import ChatMessage

class LocalChatStorage(ChatStorage):
    """In-memory implementation of ChatStorage using a dictionary cache.
    
    This class provides a simple in-memory storage solution for chat messages.
    The storage is volatile and will be cleared when the program terminates.
    """
    
    cache: Dict[str, List[ChatMessage]] = {}
    
    async def get_history(self, chat_id: str) -> List[ChatMessage]:
        """Retrieve the chat history for a given chat ID from the in-memory cache.
        
        Args:
            chat_id: The unique identifier for the chat session
            
        Returns:
            List[ChatMessage]: A deep copy of the list of chat messages in the conversation.
            Returns an empty list if no history exists for the chat_id.
        """
        return copy.deepcopy(self.cache.get(chat_id, []))
    
    async def update_history(self, chat_id: str, messages: List[ChatMessage]) -> None:
        """Update the chat history for a given chat ID in the in-memory cache.
        
        Args:
            chat_id: The unique identifier for the chat session
            messages: The list of chat messages to store
        """
        self.cache[chat_id] = messages

    async def append_history(self, chat_id: str, messages: List[ChatMessage]) -> None:
        """Append new messages to the existing chat history in the in-memory cache.
        
        Args:
            chat_id: The unique identifier for the chat session
            messages: The list of new chat messages to append to the existing history
        """
        existing_history = await self.get_history(chat_id)
        self.cache[chat_id] = existing_history + messages
