#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "requests>=2.34.2",
# ]
# ///

from dataclasses import dataclass, field
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
    cooldown: int


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

# Minimum time (in seconds) between two hook runs, so they don't fire repeatedly
cooldown = 14400
"""

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


@dataclass
class Detector:
    config: Config
    trg_messages: list[tuple[str, int]] = field(default_factory=list)
    reactions: dict[tuple[str, int], set[str]] = field(default_factory=dict)
    last_fired: float | None = None

    def should_fire(self, env: Envelope) -> bool:
        if not self._threshold_reached(env):
            return False
        now = time.monotonic()
        if self.last_fired is not None:
            remaining = self.config["cooldown"] - (now - self.last_fired)
            if remaining > 0:
                print(f"Triggered during cooldown, {remaining:.0f}s left", flush=True)
                return False
        self.last_fired = now
        self.trg_messages.clear()
        self.reactions.clear()
        return True

    def _threshold_reached(self, env: Envelope) -> bool:
        cutoff_ms = time.time_ns() // 1_000_000 - self.config["window"] * 1000
        data = env.get("dataMessage", {})

        if text := data.get("message"):
            if text.lower().strip() != self.config["trigger_msg"]:
                return False
            self.trg_messages.append((env["sourceUuid"], env["timestamp"]))
            self.trg_messages = [m for m in self.trg_messages if m[1] > cutoff_ms]
            return len(self.trg_messages) >= self.config["msg_count"]

        if reaction := data.get("reaction"):
            key = (reaction["targetAuthorUuid"], reaction["targetSentTimestamp"])
            self.reactions = {
                k: v for k, v in self.reactions.items() if k[1] > cutoff_ms
            }
            if key[1] <= cutoff_ms:
                return False
            reactors = self.reactions.setdefault(key, set())
            if reaction["isRemove"]:
                reactors.discard(env["sourceUuid"])
            else:
                reactors.add(env["sourceUuid"])
            return len(reactors) >= self.config["emoji_count"]

        return False


def listen(config: Config, detector: Detector):
    with requests.get(config["events_url"], stream=True, timeout=(5, None)) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            line = line.decode()
            if not line or not line.startswith("data:"):
                continue

            event: ModelItem = json.loads(line[5:])
            with open("events.jsonl", "a") as f:
                f.write(json.dumps(event) + "\n")

            if detector.should_fire(event.get("envelope", {})):
                fire_all()


def main():
    # Make SIGTERM run our finally/cleanup instead of killing silently.
    def handle_sigterm(*args):
        raise SystemExit

    signal.signal(signal.SIGTERM, handle_sigterm)

    config = load_config()
    if not hooks():
        raise SystemExit(f"No executable hooks in {HOOKS_DIR}")

    detector = Detector(config)
    while True:
        try:
            listen(config, detector)
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Disconnected ({e}), retrying in 5s", flush=True)
            time.sleep(5)


if __name__ == "__main__":
    main()
