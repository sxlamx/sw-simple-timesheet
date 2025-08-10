import os
from typing import Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Simple Timesheet"
    API_V1_STR: str = "/api/v1"
    
    # Database Configuration
    DATABASE_URL: str = "sqlite:///./db/timesheet.db"  # Fallback to SQLite if PostgreSQL not configured
    
    # PostgreSQL Database Configuration (optional, will build DATABASE_URL if provided)
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Build PostgreSQL URL if all components are provided
        if all([self.POSTGRES_USER, self.POSTGRES_PASSWORD, self.POSTGRES_HOST, self.POSTGRES_PORT, self.POSTGRES_DB]):
            self.DATABASE_URL = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: str = "http://localhost:8095/api/v1/auth/callback"
    
    # Google Sheets
    GOOGLE_SHEETS_CREDENTIALS_FILE: Optional[str] = None
    GOOGLE_SHEETS_SCOPES: list = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    
    # JWT
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:5185"
    
    # Environment
    DEBUG: bool = True
    
    # Email configuration
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@simpletimesheet.com"
    FRONTEND_URL: str = "http://localhost:5185"
    
    class Config:
        case_sensitive = True
        # Use Docker-specific env file if running in container, otherwise use development
        env_file = "/app/.env.docker" if os.path.exists("/app/.env.docker") else ".env.development"
        env_file_encoding = 'utf-8'

settings = Settings()