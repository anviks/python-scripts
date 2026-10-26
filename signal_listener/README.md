# Signal Listener

Listens to selected conversations in Signal for messages and reactions, and upon reaching the configured amount of certain messages or reactions, runs custom scripts. The purpose of this is to provide the possibility for custom notification handling for advanced/specific situations in Signal conversations, since in Signal itself, it's only possible to configure notifications per-conversation, but not per-message. As usual, if you want me to extend the functionality, open an issue about it and I will be glad to do it.

## Requirements

- [uv](https://docs.astral.sh/uv/)
- A running [signal-cli](https://github.com/AsamK/signal-cli) instance

## Installation

```sh
uv tool install "git+https://github.com/anviks/python-scripts#subdirectory=signal_listener"
```

## Usage

```sh
signal-listener
```

## Configuration

On the first run, [config.example.toml](src/signal_listener/config.example.toml) is copied to `~/.config/signal-listener/config.toml`. Change it according to your needs. In addition, `~/.config/signal-listener/hooks.d` directory is created - place any scripts there that you want to run when signal-listener is triggered; and make sure they're all executable.
