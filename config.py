from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Purplle Store Intelligence API"
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "sqlite:///./store_intelligence.db"
    
    # AI Engine Thresholds
    QUEUE_CRITICAL_DEPTH: int = 5
    CONVERSION_WARN_THRESHOLD: float = 10.0
    
    class Config:
        env_file = ".env"

settings = Settings()
