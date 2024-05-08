"""Mock `pymodbus` utils."""

from typing import Any


def getnext(iterable: list, default: Any = 0):
    """Yield one item at a time and yield `default` when iterable is exhausted."""

    yield from iterable
    while True:
        yield default
