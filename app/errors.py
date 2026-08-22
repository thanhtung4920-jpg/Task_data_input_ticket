import sqlite3

from PySide6.QtWidgets import QMessageBox

from app.config import ConfigError
from app.master_data import MasterDataError


def show_error(parent, title, message):
    QMessageBox.critical(parent, title, message)


def safe_call(fn, parent=None, title="Error"):
    """Run fn(). On known DB/master-data failures, show a clear message
    instead of crashing or leaving a half-done write. Returns True on
    success, False if a handled error occurred."""
    try:
        fn()
        return True
    except sqlite3.Error as e:
        show_error(
            parent,
            title,
            "Could not reach the task database on the shared drive. "
            "Check the network connection and try again.\n\nDetails: " + str(e),
        )
        return False
    except MasterDataError as e:
        show_error(
            parent,
            title,
            "Could not load master data from the shared drive.\n\nDetails: " + str(e),
        )
        return False
    except ConfigError as e:
        show_error(
            parent,
            title,
            "Could not read the application configuration file.\n\nDetails: " + str(e),
        )
        return False


def safe_get(fn, default=None, parent=None, title="Error"):
    """Run fn() and return its result. On a handled error, show the message
    (via safe_call) and return `default` instead."""
    result = {}
    ok = safe_call(lambda: result.update(value=fn()), parent=parent, title=title)
    return result["value"] if ok else default
