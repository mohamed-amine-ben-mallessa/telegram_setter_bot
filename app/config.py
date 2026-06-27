from pathlib import Path
from pydantic_settings import BaseSettings
import yaml

class Settings(BaseSettings):
    API_ID: str = ""
    API_HASH: str = ""
    BOT_TOKEN: str = ""
    SESSION_NAME: str = "setter_session"
    SESSION_STRING: str = ""
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4.1-mini"
    DATABASE_URL: str = "sqlite:///./data/leads.db"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

BASE_DIR = Path(__file__).resolve().parents[1]
CONFIG_DIR = BASE_DIR / "config"

def load_yaml(name: str) -> dict:
    path = CONFIG_DIR / name
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)