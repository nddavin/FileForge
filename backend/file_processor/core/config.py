from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # App settings
    app_name: str = "FileForge"
    version: str = "1.0.0"
    debug: bool = False

    # Security
    secret_key: str = "dev-secret-key"
    encryption_key: str = "dev-encryption-key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Database
    database_url: str = "sqlite:///./app.db"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # File storage
    upload_dir: str = "./uploads"
    processed_dir: str = "./processed"

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # External services
    sentry_dsn: str = ""

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_role_key: str = ""
    supabase_jwt_secret: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
