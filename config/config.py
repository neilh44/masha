# config.py
import os
from typing import Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Base Configuration
    APP_NAME = "AI Appointment Management System"
    VERSION = "1.0.0"
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Server Configuration
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    WORKERS = int(os.getenv("WORKERS", 4))
    
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL")
    DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", 20))
    DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", 10))
    
    # Security Configuration
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")
    CORS_METHODS = ["*"]
    CORS_HEADERS = ["*"]
    
    # AI Model Configuration
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    MODEL_NAME = "llama-3-8b-8192"
    MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", 0.3))
    MAX_TOKENS = int(os.getenv("MAX_TOKENS", 500))
    
    # Voice Service Configuration
    DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")
    VOICE_SAMPLE_RATE = int(os.getenv("VOICE_SAMPLE_RATE", 24000))
    DEFAULT_VOICE = os.getenv("DEFAULT_VOICE", "female-1")
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE = "app.log"
    
    # Session Configuration
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", 3600))  # 1 hour
    MAX_SESSION_SIZE = int(os.getenv("MAX_SESSION_SIZE", 1000))
    
    @classmethod
    def get_all_settings(cls) -> Dict[str, Any]:
        """Get all configuration settings as a dictionary"""
        return {
            key: value for key, value in cls.__dict__.items()
            if not key.startswith('_') and not callable(value)
        }
