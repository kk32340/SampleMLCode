import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration settings for the Teams bot"""
    
    # Bot Framework settings
    MICROSOFT_APP_ID = os.getenv("MICROSOFT_APP_ID", "")
    MICROSOFT_APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD", "")
    MICROSOFT_APP_TENANT_ID = os.getenv("MICROSOFT_APP_TENANT_ID", "")
    
    # Server settings
    PORT = int(os.getenv("PORT", 3978))
    HOST = os.getenv("HOST", "0.0.0.0")
    
    # AI Model settings
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash-latest")
    
    # Optional: Document processing settings
    MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", 10))
    SUPPORTED_FILE_TYPES = [".txt", ".pdf", ".docx", ".xlsx", ".csv", ".json", ".md"]
    
    # Conversation settings
    MAX_CONVERSATION_HISTORY = int(os.getenv("MAX_CONVERSATION_HISTORY", 20))
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        required_vars = []
        
        if not cls.GEMINI_API_KEY:
            required_vars.append("GEMINI_API_KEY")
        
        # For production deployment, these are required
        # if not cls.MICROSOFT_APP_ID:
        #     required_vars.append("MICROSOFT_APP_ID")
        # if not cls.MICROSOFT_APP_PASSWORD:
        #     required_vars.append("MICROSOFT_APP_PASSWORD")
        
        if required_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(required_vars)}")
        
        return True

# Validate configuration on import
Config.validate() 