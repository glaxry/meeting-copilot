from functools import lru_cache
from pathlib import Path

from pydantic import BaseModel, Field


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


class Settings(BaseModel):
    app_name: str = "Meeting Copilot"
    app_version: str = "0.2.0-day2"
    repo_root: Path = Field(default_factory=_repo_root)
    data_dir: Path = Field(default_factory=lambda: _repo_root() / "data")
    annotations_dir: Path = Field(default_factory=lambda: _repo_root() / "data" / "annotations")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
