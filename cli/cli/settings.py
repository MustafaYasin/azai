from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_USERNAME: str
    POSTGRES_PASSWORD: str
    POSTGRES_DATABASE: str
    POSTGRES_HOST: str

    OPENAI_KEY: str

    APP_PASSWORD: str

    MODEL: str = "gpt-4"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    MAX_TOKENS: int = 8191
    MERGE_PEERS: bool = True


load_dotenv()

settings = Settings()

def get_openai_api_key():
    return settings.OPENAI_KEY
