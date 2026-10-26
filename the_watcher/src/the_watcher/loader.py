import os
from pathlib import Path
import tomllib
from typing import TypedDict

import msgspec
from platformdirs import user_config_dir, user_state_dir


class Config(TypedDict):
    movies: list[int]
    tmdb_token: str
    webhook_url: str


state_dir = Path(os.getenv("STATE_DIRECTORY") or user_state_dir("the-watcher"))
config_path = (
    Path(os.getenv("CONFIGURATION_DIRECTORY") or user_config_dir("the-watcher"))
    / "config.toml"
)


def is_notified(kind: str, key: str) -> bool:
    return (state_dir / kind / key).exists()


def mark_notified(kind: str, key: str) -> None:
    (state_dir / kind).mkdir(parents=True, exist_ok=True)
    (state_dir / kind / key).touch()


def load_config() -> Config:
    if not config_path.exists():
        config_path.parent.mkdir(parents=True, exist_ok=True)
        (Path(__file__).parent / "config.example.toml").copy(config_path)
        config_path.chmod(0o600)
        raise SystemExit(f"Created {config_path}, fill it in and run again")
    try:
        config = msgspec.convert(tomllib.loads(config_path.read_text()), type=Config)
    except (tomllib.TOMLDecodeError, msgspec.ValidationError) as e:
        raise SystemExit(f"Invalid config in {config_path}: {e}")
    if not config["webhook_url"]:
        raise SystemExit(f"Set webhook_url in {config_path}")
    return config
