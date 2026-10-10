import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Database Configuration (Supabase PostgreSQL)
    DATABASE_URL: str = ""

    # LLM Service (Groq Cloud)
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "qwen/qwen3.8-27b"
    GROQ_ENDPOINT: str = "https://api.groq.com/openai/v1/chat/completions"

    # RapidAPI Service (Booking.com)
    RAPIDAPI_KEY: str = ""
    RAPIDAPI_HOST: str = "booking-com15.p.rapidapi.com"

    # Datasets
    BUSES_DATA_PATH: str = str(BASE_DIR / "data" / "buses.json")

    # JWT Authentication
    JWT_SECRET_KEY: str = "traveltech_secret_jwt_key_change_in_production_32bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
