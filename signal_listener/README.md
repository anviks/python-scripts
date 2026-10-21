## Dependencies

- `uv` - https://docs.astral.sh/uv/getting-started/installation/

## Installation

```bash
SIGNAL_LISTENER_BIN_PATH=~/.local/bin/signal-listener
export SIGNAL_LISTENER_CONFIG_DIR=~/.config/signal_listener  # Script reads this 

curl -fsSL -o "$SIGNAL_LISTENER_BIN_PATH" https://raw.githubusercontent.com/anviks/python-scripts/main/signal_listener/listen.py
chmod +x "$SIGNAL_LISTENER_BIN_PATH"

# Creating config (skip if you already have the config files)
"$SIGNAL_LISTENER_BIN_PATH"  # Creates config.toml and exits if it doesn't exist yet
mkdir "$SIGNAL_LISTENER_CONFIG_DIR/hooks.d" # Place any scripts here that you want to run when signal-listener is triggered, and make sure they're all executable (chmod +x <file>)

# Now just run the program (or create a systemd service)
"$SIGNAL_LISTENER_BIN_PATH"
```
