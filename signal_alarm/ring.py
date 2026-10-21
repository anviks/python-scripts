import json
import os
import subprocess
import time

ALARM = os.path.expanduser("~/thomas_the_train.opus")
FLAG = os.path.expanduser("~/.alarm_stop")
NOTIF_ID = "alarm"
POLL_INTERVAL = 1  # Second between checks about running sound status
ALARM_COOLDOWN = (
    6 * 60 * 60
)  # Minimum time between two alarms being triggered; if this number is smaller than TRG_WINDOW, old messages will count towards the next alarm

prev_alarm_time = 0.0


def run(cmd: list[str]):
    """Run a command without raising on a non-zero exit."""
    return subprocess.run(cmd, capture_output=True, text=True)


def is_playing():
    return "Status: Playing" in run(["termux-media-player", "info"]).stdout


def start_playback():
    run(["termux-media-player", "play", ALARM])


def post_notification():
    run(
        [
            "termux-notification",
            "--id",
            NOTIF_ID,
            "--title",
            "⏰ Alarm ringing",
            "--content",
            "Tap Stop to silence",
            "--priority",
            "max",
            "--ongoing",  # non-swipeable; stays until Stop
            "--button1",
            "Stop",
            "--button1-action",
            f"touch {FLAG}",
        ]
    )


def remove_flag():
    try:
        os.remove(FLAG)
    except FileNotFoundError:
        pass


def get_music_stream():
    streams = json.loads(run(["termux-volume"]).stdout)
    return next(s for s in streams if s["stream"] == "music")


def get_volume():
    return get_music_stream()["volume"]


def set_volume(val: int):
    run(["termux-volume", "music", str(val)])


def get_max_volume():
    return get_music_stream()["max_volume"]


def increment_volume():
    if (vol := get_volume()) < get_max_volume():
        set_volume(vol + 1)


def cleanup():
    run(["termux-media-player", "stop"])
    run(["termux-notification-remove", NOTIF_ID])
    set_volume(initial_volume)
    run(["termux-wake-unlock"])
    remove_flag()


def run_alarm():
    global initial_volume, prev_alarm_time

    if time.time() - prev_alarm_time < ALARM_COOLDOWN:
        return

    run(["termux-wake-lock"])
    initial_volume = get_volume()
    set_volume(1)
    post_notification()
    start_time = prev_alarm_time = time.time()

    try:
        while not os.path.exists(FLAG):
            if time.time() - start_time > 10:
                increment_volume()
                start_time = time.time()
            if not is_playing():
                start_playback()
            time.sleep(POLL_INTERVAL)
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        cleanup()
