from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    app_name: str = "Audio Transcription Pipeline"
    api_prefix: str = ""

    data_dir: Path = Path("data")
    upload_dir: Path = Path("data/uploads")
    normalized_dir: Path = Path("data/normalized")
    database_path: Path = Path("data/transcriptions.db")

    whisper_model: str = "base"
    device: str = "auto"
    fp16: bool = True

    allowed_extensions: set[str] = {
        ".mp3",
        ".wav",
        ".m4a",
        ".flac",
        ".ogg",
        ".oga",
        ".mp4",
        ".webm",
        ".aac",
    }
    max_upload_mb: int = 500

    target_sample_rate: int = 16000
    target_channels: int = 1


settings = Settings()

for path in (settings.data_dir, settings.upload_dir, settings.normalized_dir):
    path.mkdir(parents=True, exist_ok=True)
settings.database_path.parent.mkdir(parents=True, exist_ok=True)
