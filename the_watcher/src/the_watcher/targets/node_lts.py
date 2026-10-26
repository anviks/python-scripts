import subprocess
from warnings import warn
import requests
from ..loader import is_notified, mark_notified


def get_node_lts() -> str:
    versions = requests.get("https://nodejs.org/dist/index.json").json()
    for version in versions:
        if version["lts"] != False:
            return version["version"]
    raise RuntimeError("Not a single LTS version found")


def get_node_lts_docker() -> str | None:
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
    )

    if process.returncode == 0:
        return process.stdout.decode().strip()
    return None


def check_node_lts(webhook_url: str):
    cur_ver = get_node_lts()
    if not is_notified("node_lts", cur_ver):
        requests.post(webhook_url, json={"content": f"Node {cur_ver} has entered LTS"})
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
            )
            mark_notified("node_lts_docker", cur_ver_docker)
