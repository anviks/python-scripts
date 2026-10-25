# The Watcher

Small one-shot checks that post to a Discord webhook when something I care about changes. Each run checks a single target, compares the result with the last known state and exits, so it's meant to be run on a schedule (cron, systemd timer).

## Targets

| Target     | What it watches                                                                                                  |
|------------|------------------------------------------------------------------------------------------------------------------|
| `movies`   | Movies from TMDB. Notifies once a movie becomes available on any streaming/rent/buy provider, with its poster and the list of providers. |
| `node_lts` | Node.js releases. Notifies when a new version enters LTS, and when the `node:lts-alpine` Docker image picks it up. |

## Requirements

- Python 3.14+ and [uv](https://docs.astral.sh/uv/)
- A Discord [webhook URL](https://support.discord.com/hc/en-us/articles/228383668)
- `movies`: a [TMDB API read access token](https://www.themoviedb.org/settings/api)
- `node_lts`: Docker, for checking the Node version inside `node:lts-alpine`

## Installation

```sh
uv tool install "git+https://github.com/anviks/python-scripts#subdirectory=the_watcher"
```

## Usage

```sh
the-watcher movies
the-watcher node_lts
```

## Configuration

On the first run, [config.example.toml](src/the_watcher/config.example.toml) is copied to `~/.config/the-watcher/config.toml`. Fill it in.

The config holds secrets, so it's a good idea to make it readable only by you:

```sh
chmod 600 ~/.config/the-watcher/config.toml
```

A movie's id is the number in its TMDB URL, e.g. `https://www.themoviedb.org/movie/1003596-avengers-doomsday`.

## State

What has already been notified about is stored in `~/.local/state/the-watcher/state.json`. Delete an entry (or the whole file) to get notified again.

## File locations

| File          | Default location                         | Overridden by                                      |
|---------------|------------------------------------------|----------------------------------------------------|
| `config.toml` | `~/.config/the-watcher/`                 | `$CONFIGURATION_DIRECTORY`, `$XDG_CONFIG_HOME`     |
| `state.json`  | `~/.local/state/the-watcher/`            | `$STATE_DIRECTORY`, `$XDG_STATE_HOME`              |

`CONFIGURATION_DIRECTORY` and `STATE_DIRECTORY` are set by systemd when the unit uses `ConfigurationDirectory=` / `StateDirectory=`, and they point straight at the directory (no `the-watcher` suffix is added).
