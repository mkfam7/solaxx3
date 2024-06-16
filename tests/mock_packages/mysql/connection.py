"""Module containing a connection class."""

from pathlib import Path

from .cursor import Cursor
from .error import Error

open_connections_file = Path(__file__).parent / "open_connections.txt"


class Connection:
    """Class mocking a connection to a MySQL server."""

    def __init__(self, *args, consider_open=True, **kwargs):
        self.open_connections += consider_open
        self.open: bool = consider_open

    def cursor(self) -> Cursor:
        """Return the cursor for the connection."""

        self._cursor = Cursor()
        return self._cursor

    def close(self):
        """Close connection."""

        if not self.open:
            raise Error("Connection already closed")

        self.open = False
        self.open_connections -= 1

    def commit(self):
        """Save all changes to the database."""

    def is_connected(self) -> bool:
        """Return if the connection is open."""

        return self.open

    @property
    def open_connections(self):
        with open(open_connections_file, "r", encoding="utf-8") as f:
            contents = f.read()
            return int(contents)

    @open_connections.setter
    def open_connections(self, value: int):
        value = value if value > 0 else 0
        with open(open_connections_file, "w", encoding="utf-8") as f:
            f.write(str(value))
