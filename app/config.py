import json
import os

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json"
)


class ConfigError(Exception):
    pass


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except OSError as e:
        raise ConfigError(f"Could not read config file: {CONFIG_PATH} ({e})") from e
    except json.JSONDecodeError as e:
        raise ConfigError(f"Config file is not valid JSON: {CONFIG_PATH} ({e})") from e
