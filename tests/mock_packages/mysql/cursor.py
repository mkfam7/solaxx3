"""Module with cursor implementation."""

import json
from pathlib import Path
from .error import Error


config_file = Path(__file__).parent / "cursor_config.json"


class Cursor:
    """Cursor of a MySQL connection."""

    def __init__(self, raise_err: bool = True):
        if self._raise_error_in_init and raise_err:
            raise Error

    def execute(self, *args, **kwargs) -> None:
        """Mock execute a query."""

        if self._raise_error:
            raise Error

    def executemany(self, *args, **kwargs) -> None:
        """Mock execute a query multiple times with different data."""

        if self._raise_error:
            raise Error

    @property
    def _raise_error(self):
        return self._read_configs()["raise_error"]

    @property
    def _raise_error_in_init(self):
        return self._read_configs()["raise_error_in_init"]

    @_raise_error.setter
    def _raise_error(self, value: int):
        data = self._read_configs()
        data["raise_error"] = value
        self._save_configs(data)

    @_raise_error_in_init.setter
    def _raise_error_in_init(self, value: int):
        data = self._read_configs()
        data["raise_error_in_init"] = value
        self._save_configs(data)

    def _read_configs(self):
        with open(config_file, "r", encoding="utf-8") as f:
            return json.loads(f.read())

    def _save_configs(self, data):
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(json.dumps(data, indent=4))
