from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

root_dir = Path(__file__).parent.parent.parent

class Settings(BaseSettings):
    app_password: str
    openai_key: str

    media_dir: Path = root_dir / "media"

load_dotenv()
settings = Settings()
