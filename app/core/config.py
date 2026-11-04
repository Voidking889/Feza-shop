from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    PROJECT_NAME: str = "MyFeza Backend"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database 
    DATABASE_URL: str = f"sqlite+aiosqlite:///{(BASE_DIR / 'data' / 'feza_shop.sqlite3').as_posix()}"

    # API Keys
    STRIPE_SECRET_KEY: str = ""
    NMB_API_KEY: str | None = None
    NMB_CONSUMER_SECRET: str | None = None
    NMB_CONSUMER_ID: str | None = None
    
    # Flutterwave
    FLUTTERWAVE_PUBLIC_KEY: str = ""
    FLUTTERWAVE_SECRET_KEY: str = ""
    
    # Email / SMTP Settings
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 587
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_FROM_NAME: str = "Feza Shop"

    model_config = SettingsConfigDict(env_file=BASE_DIR / ".env", case_sensitive=True, extra="allow")

settings = Settings()
