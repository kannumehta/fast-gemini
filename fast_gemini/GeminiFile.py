from pydantic import BaseModel

class GeminiFile(BaseModel):
    """Model representing a file to be sent to Gemini API."""
    uri: str
    mime_type: str 