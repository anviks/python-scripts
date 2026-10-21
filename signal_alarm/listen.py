#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "requests>=2.34.2",
# ]
# ///

import json
import signal
import time
import tomllib
from typing import NotRequired, TypedDict, cast
import os
import subprocess
from pathlib import Path

import requests

### Types


class TypingMessage(TypedDict):
    action: str
    timestamp: int
    groupId: NotRequired[str]


class GroupInfo(TypedDict):
    groupId: str
    groupName: str
    revision: int
    type: str


class Reaction(TypedDict):
    emoji: str
    targetAuthor: str
    targetAuthorNumber: str
    targetAuthorUuid: str
    targetSentTimestamp: int
    isRemove: bool


class DataMessage(TypedDict):
    timestamp: int
    message: str | None
    expiresInSeconds: int
    isExpirationUpdate: bool
    viewOnce: bool
    isEndSession: bool
    isProfileKeyUpdate: bool
    hasProfileKey: bool
    groupInfo: NotRequired[GroupInfo]
    reaction: NotRequired[Reaction]


class Envelope(TypedDict):
    source: str
    sourceNumber: str | None
    sourceUuid: str
    sourceName: str
    sourceDevice: int
    timestamp: int
    serverReceivedTimestamp: int
    serverDeliveredTimestamp: int
    typingMessage: NotRequired[TypingMessage]
    dataMessage: NotRequired[DataMessage]


class ModelItem(TypedDict):
    envelope: Envelope
    account: str


class Config(TypedDict):
    events_url: str
    trigger_msg: str
    msg_count: int
    emoji_count: int
    window: int


### Constants
CONFIG_DIR = Path(
    os.getenv("SIGNAL_LISTENER_CONFIG_DIR", "~/.config/signal_listener")
).expanduser()
CONFIG_PATH = CONFIG_DIR / "config.toml"
HOOKS_DIR = CONFIG_DIR / "hooks.d"
CONFIG_TEMPLATE = """\
events_url = "http://<signal-api-host>:9000/api/v1/events"

trigger_msg = "hi"

# this many trigger messages within the window...
msg_count = 5

# ...or this many reactions on one message (max one reaction per person) will trigger the hooks
emoji_count = 5

# Time window (in seconds) for triggering messages and emojis to appear
window = 7200
"""


### Global variables
msg_counter = 0
reactions: dict[tuple[str, int], set[str]] = {}
trg_messages: list[tuple[str, int]] = []

# TODO: Add a cooldown, an alarm shouldn't be triggered many times in a few minutes/hours
# TODO: Add a channel filter


def load_config() -> Config:
    if not CONFIG_PATH.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(CONFIG_TEMPLATE)
        raise SystemExit(f"Created {CONFIG_PATH}, fill it in and run again")
    config = tomllib.loads(CONFIG_PATH.read_text())
    if missing := [k for k in Config.__required_keys__ if k not in config]:
        raise SystemExit(f"Missing keys in {CONFIG_PATH}: {', '.join(sorted(missing))}")
    return cast(Config, config)


def hooks() -> list[Path]:
    if not HOOKS_DIR.is_dir():
        return []
    return sorted(
        p for p in HOOKS_DIR.iterdir() if p.is_file() and os.access(p, os.X_OK)
    )


def fire_all():
    for hook in hooks():
        try:
            subprocess.Popen(
                [hook], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            print(f"Ran hook {hook.name}", flush=True)
        except OSError as e:
            print(f"Hook {hook.name} failed: {e}", flush=True)


def listen(config: Config):
    global msg_counter, trg_messages, reactions

    with requests.get(config["events_url"], stream=True, timeout=(5, None)) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            line = line.decode()
            if not line or not line.startswith("data:"):
                continue

            event: ModelItem = json.loads(line[5:])
            with open("events.jsonl", "a") as f:
                f.write(json.dumps(event) + "\n")

            cutoff_ms = time.time_ns() // 1_000_000 - config["window"] * 1000

            env = event.get("envelope", {})
            if text := env.get("dataMessage", {}).get("message"):
                if text.lower().strip() == config["trigger_msg"]:
                    trg_messages.append((env["sourceUuid"], env["timestamp"]))
                    trg_messages = [m for m in trg_messages if m[1] > cutoff_ms]
                    if len(trg_messages) >= config["msg_count"]:
                        fire_all()
            elif reaction := env.get("dataMessage", {}).get("reaction"):
                key = (reaction["targetAuthorUuid"], reaction["targetSentTimestamp"])
                reactor = env["sourceUuid"]

                reactions = {k: v for k, v in reactions.items() if k[1] > cutoff_ms}
                if key[1] <= cutoff_ms:
                    continue

                reactors = reactions.setdefault(key, set())
                if reaction["isRemove"]:
                    reactors.discard(reactor)
                else:
                    reactors.add(reactor)

                if len(reactors) >= config["emoji_count"]:
                    fire_all()


def main():
    # Make SIGTERM run our finally/cleanup instead of killing silently.
    def handle_sigterm(*args):
        raise SystemExit

    signal.signal(signal.SIGTERM, handle_sigterm)

    config = load_config()
    if not hooks():
        raise SystemExit(f"No executable hooks in {HOOKS_DIR}")

    while True:
        try:
            listen(config)
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Disconnected ({e}), retrying in 5s", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
