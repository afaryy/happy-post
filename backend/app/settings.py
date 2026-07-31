import os
from dataclasses import dataclass, field


def optional_environment_value(name: str) -> str | None:
    return os.getenv(name) or None


def application_version() -> str:
    return os.getenv("APP_VERSION", "0.1.0")


def database_url() -> str | None:
    return optional_environment_value("DATABASE_URL")


@dataclass(frozen=True)
class Settings:
    app_version: str = field(default_factory=application_version)
    database_url: str | None = field(default_factory=database_url)
