# The Watcher

Small one-shot checks that post to a Discord webhook when something I care about changes. Each run checks a single target, compares the result with the last known state and exits, so it's meant to be run on a schedule (cron, systemd timer).

## Targets

| Target     | What it watches                                                                                                  |
|------------|------------------------------------------------------------------------------------------------------------------|
| `movies`   | Movies from TMDB. Notifies once a movie becomes available on any streaming/rent/buy provider, with its poster and the list of providers. |
| `node_lts` | Node.js releases. Notifies when a new version enters LTS, and when the `node:lts-alpine` Docker image picks it up. |
