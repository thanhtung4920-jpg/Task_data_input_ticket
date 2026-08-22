import json

from app.config import load_config

REQUIRED_KEYS = ["Activity", "ProjectName", "USERID", "Status"]


class MasterDataError(Exception):
    pass


def load_master_data():
    config = load_config()
    path = config["master_data_path"]

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except OSError as e:
        raise MasterDataError(f"Master data file could not be read: {path} ({e})") from e
    except json.JSONDecodeError as e:
        raise MasterDataError(f"Master data file is not valid JSON: {path}") from e

    missing = [key for key in REQUIRED_KEYS if key not in data]
    if missing:
        raise MasterDataError(f"Master data file is missing keys: {missing}")

    invalid = [
        key
        for key in REQUIRED_KEYS
        if not isinstance(data[key], list) or not all(isinstance(item, str) for item in data[key])
    ]
    if invalid:
        raise MasterDataError(
            f"Master data file has invalid values (expected a list of strings) for: {invalid}"
        )

    return {key: data[key] for key in REQUIRED_KEYS}
