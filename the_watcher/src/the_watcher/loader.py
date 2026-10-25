import json
import os
from pathlib import Path
import tomllib
from typing import TypedDict, cast


class Config(TypedDict):
    movies: list[int]
    tmdb_token: str
    webhook_url: str


class NodeLts(TypedDict):
    version: str
    version_docker: str


class State(TypedDict):
    node_lts: NodeLts
    movies: list[int]


def _dir(env: str, xdg: str, default: str) -> Path:
    if d := os.getenv(env):
        return Path(d)
    return Path(os.getenv(xdg, Path.home() / default)) / "the-watcher"


state_path = _dir("STATE_DIRECTORY", "XDG_STATE_HOME", ".local/state") / "state.json"
config_path = (
    _dir("CONFIGURATION_DIRECTORY", "XDG_CONFIG_HOME", ".config") / "config.toml"
)


def load_state() -> State:
    if not state_path.exists():
        default_state: State = {
            "movies": [],
            "node_lts": {"version": "", "version_docker": ""},
        }
        state_path.parent.mkdir(parents=True)
        state_path.write_text(json.dumps(default_state))

    return json.loads(state_path.read_text())


def save_state(state: State) -> None:
    state_path.write_text(json.dumps(state, indent=4))


def load_config() -> Config:
    if not config_path.exists():
        config_path.parent.mkdir(parents=True)
        (Path(__file__).parent / "config.example.toml").copy(config_path)
    return cast(Config, tomllib.loads(config_path.read_text()))
