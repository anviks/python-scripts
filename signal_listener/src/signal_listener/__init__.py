from dataclasses import dataclass, field
import json
import re
import signal
import time
import subprocess

import requests

from .config import load_config, load_hooks, hooks_dir
from .types import Config, Envelope, ModelItem


PHONE_RE = re.compile(r"^\+\d+$")
UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I
)


def validate_channels(config: Config):
    if not config["channels"]:
        return
    base = config["api_url"].rstrip("/")
    try:
        known: set[str] = set()
        accounts = requests.get(f"{base}/accounts", timeout=5)
        accounts.raise_for_status()
        for number in accounts.json():
            groups = requests.get(f"{base}/groups/{number}", timeout=5)
            groups.raise_for_status()
            for g in groups.json():
                known.update(
                    filter(None, (g.get("name"), g.get("id"), g.get("internal_id")))
                )
    except (requests.RequestException, ValueError, AttributeError) as e:
        print(f"Couldn't validate channels against the API ({e}), skipping", flush=True)
        return
    for entry in config["channels"]:
        if entry in known or PHONE_RE.match(entry) or UUID_RE.match(entry):
            continue
        print(
            f'Warning: channel "{entry}" matches no known group name/ID, '
            "phone number or UUID (typo?)",
            flush=True,
        )


def fire_all():
    for hook in load_hooks():
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
    ignored: set[str] = field(default_factory=set)

    def should_fire(self, env: Envelope) -> bool:
        if not self._in_channels(env) or not self._threshold_reached(env):
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

    def _in_channels(self, env: Envelope) -> bool:
        if not self.config["channels"]:
            return True
        if group := env.get("dataMessage", {}).get("groupInfo"):
            key = group["groupId"]
            ok = (
                key in self.config["channels"]
                or group.get("groupName") in self.config["channels"]
            )
            desc = f'group "{group.get("groupName")}" (id {key})'
        else:
            key = env.get("sourceUuid", "")
            ok = (
                env.get("sourceNumber") in self.config["channels"]
                or key in self.config["channels"]
            )
            desc = f"sender {env.get('sourceNumber') or key}"
        if not ok and key not in self.ignored:
            self.ignored.add(key)
            print(f"Ignoring {desc}, not in channels", flush=True)
        return ok

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
    events_url = f"{config['api_url'].rstrip('/')}/events"
    with requests.get(events_url, stream=True, timeout=(5, None)) as r:
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


def main() -> None:
    # Make SIGTERM run our finally/cleanup instead of killing silently.
    def handle_sigterm(*_):
        raise SystemExit

    signal.signal(signal.SIGTERM, handle_sigterm)

    config = load_config()
    if not load_hooks():
        raise SystemExit(f"No executable hooks in {hooks_dir}")

    validate_channels(config)
    detector = Detector(config)
    while True:
        try:
            listen(config, detector)
        except (requests.RequestException, json.JSONDecodeError) as e:
            print(f"Disconnected ({e}), retrying in 5s", flush=True)
            time.sleep(5)
