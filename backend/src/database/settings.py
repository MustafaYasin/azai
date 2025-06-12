from dotenv import load_dotenv
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    postgres_username: str
    postgres_password: str
    postgres_database: str
    postgres_host: str

    engine_debug_echo: bool = False


load_dotenv()
settings = Settings()
