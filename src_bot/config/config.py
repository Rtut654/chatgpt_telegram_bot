from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file='.env', env_file_encoding='utf-8'
    )

    TOKEN_BOT: str

    # Mongo
    MONGO_HOST: str = '127.0.0.1'
    MONGO_PORT: int = 27017


def get_settings() -> Settings:
    return Settings()


settings = get_settings()
