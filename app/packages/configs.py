from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "task-service"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    DEBUG: bool = True

    DATABASE_URL: str
    AMQP_URL: str

    TASK_QUEUE_NAME: str = "tasks"
    TASK_QUEUE_MAX_PRIORITY: int = 10

    MAX_CONCURRENT_PROCESSES: int = 1

    TIME_TO_WAIT_TASK: int = 10


settings = Settings()  # type: ignore
