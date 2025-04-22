class GeminiClientError(Exception):
    """Base exception for Gemini client errors"""
    pass

class GeminiAPIError(GeminiClientError):
    """Exception raised for errors from the Gemini API"""
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"API Error {code}: {message}")

class GeminiResponseError(GeminiClientError):
    """Exception raised for invalid or empty responses from Gemini"""
    pass

class GeminiToolExecutionError(GeminiClientError):
    """Exception raised when tool execution fails"""
    pass 