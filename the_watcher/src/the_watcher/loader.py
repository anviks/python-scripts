import json
import os
from pathlib import Path
import tomllib
from typing import TypedDict, cast

from platformdirs import user_config_dir, user_state_dir


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


state_path = (
    Path(os.getenv("STATE_DIRECTORY") or user_state_dir("the-watcher")) / "state.json"
)
config_path = (
    Path(os.getenv("CONFIGURATION_DIRECTORY") or user_config_dir("the-watcher"))
    / "config.toml"
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
        config_path.parent.mkdir(parents=True, exist_ok=True)
        (Path(__file__).parent / "config.example.toml").copy(config_path)
    return cast(Config, tomllib.loads(config_path.read_text()))
