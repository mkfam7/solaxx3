"""Module with mock implementation of interacting with a MySQL server."""

from .connection import Connection
from .error import Error


def connect(*args, **kwargs) -> Connection:
    """Mock connect to a MySQL server."""

    return Connection()
