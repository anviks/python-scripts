import subprocess
from warnings import warn
import requests
from ..loader import is_notified, mark_notified


def get_node_lts() -> str:
    resp = requests.get("https://nodejs.org/dist/index.json", timeout=10)
    resp.raise_for_status()
    for version in resp.json():
        if version["lts"] != False:
            return version["version"]
    raise RuntimeError("Not a single LTS version found")


def get_node_lts_docker() -> str | None:
    try:
        process = subprocess.run(
            [
                "docker",
                "run",
                "--rm",
                "-q",
                "--pull",
                "always",
                "node:lts-alpine",
                "node",
                "--version",
            ],
            capture_output=True,
            timeout=300,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None

    if process.returncode == 0:
        return process.stdout.decode().strip()
    return None


def check_node_lts(webhook_url: str):
    cur_ver = get_node_lts()
    if not is_notified("node_lts", cur_ver):
        requests.post(
            webhook_url, json={"content": f"Node {cur_ver} has entered LTS"}, timeout=10
        ).raise_for_status()
        mark_notified("node_lts", cur_ver)

    # No point in running any checks if latest node version is in the image and it's been notified about
    if not is_notified("node_lts_docker", cur_ver):
        cur_ver_docker = get_node_lts_docker()
        if not cur_ver_docker:
            warn("Couldn't get node version in node:lts-alpine image")
        elif not is_notified("node_lts_docker", cur_ver_docker):
            requests.post(
                webhook_url,
                json={
                    "content": f"Docker's node:lts-alpine image upgraded its node version to {cur_ver_docker}"
                },
                timeout=10,
            ).raise_for_status()
            mark_notified("node_lts_docker", cur_ver_docker)
