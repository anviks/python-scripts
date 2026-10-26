import os
from pathlib import Path
import tomllib
from typing import cast

from .types import Config


def _dir(env: str, xdg: str, default: str) -> Path:
    if d := os.getenv(env):
        return Path(d)
    return Path(os.getenv(xdg, Path.home() / default)) / "signal-listener"


config_dir = _dir("CONFIGURATION_DIRECTORY", "XDG_CONFIG_HOME", ".config")
config_path = config_dir / "config.toml"
hooks_dir = config_dir / "hooks.d"


def load_config() -> Config:
    if not config_path.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
        hooks_dir.mkdir(exist_ok=True)
        (Path(__file__).parent / "config.example.toml").copy(config_path)
        raise SystemExit(f"Created {config_path}, fill it in and run again")
    config = tomllib.loads(config_path.read_text())
    if missing := [k for k in Config.__required_keys__ if k not in config]:
        raise SystemExit(f"Missing keys in {config_path}: {', '.join(sorted(missing))}")
    return cast(Config, config)


def load_hooks() -> list[Path]:
    if not hooks_dir.is_dir():
        return []
    return sorted(
        p for p in hooks_dir.iterdir() if p.is_file() and os.access(p, os.X_OK)
    )
