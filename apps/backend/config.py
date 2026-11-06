from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "JobPilot AI API"
    environment: str = "dev"
    database_url: str = "postgresql://jobpilot_user:jobpilot_password@localhost:5432/jobpilot_db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "super-secret-key-for-dev"
    aws_region: str = "us-east-1"
    
    class Config:
        env_file = ".env"

settings = Settings()
