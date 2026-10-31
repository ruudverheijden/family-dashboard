"""Explicit application configuration. Environment loading is opt-in at startup."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


def load_environment(env_file=None):
    load_dotenv(env_file or Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class AppConfig:
    data_dir: Path
    cache_dir: Path
    admin_password: str
    cookie_secure: bool = False
    cache_limit: int = 128 * 1024 * 1024
    background_enabled: bool = True

    @classmethod
    def from_environment(cls):
        load_environment()
        return cls(
            data_dir=Path(os.getenv("DATA_DIR", "./data")),
            cache_dir=Path(os.getenv("CACHE_DIR", "./cache")),
            admin_password=os.getenv("ADMIN_PASSWORD", ""),
            cookie_secure=os.getenv("COOKIE_SECURE", "false") == "true",
            cache_limit=int(os.getenv("CACHE_MB", "128")) * 1024 * 1024,
        )
