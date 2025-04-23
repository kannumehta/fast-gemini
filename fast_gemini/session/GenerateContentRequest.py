from typing import List, Dict
from pydantic import BaseModel
from .ChatMessage import ChatMessage

class GenerateContentRequest(BaseModel):
    contents: List[ChatMessage]
    config: Dict
