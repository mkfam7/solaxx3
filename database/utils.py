from contextlib import contextmanager
from types import ModuleType


@contextmanager
def connection(module: ModuleType, *args, save_on_close=False, **kwargs):
    """
    A method to open a connection and automatically close it even when an exception occurs.
    Must be used as a context manager.
    """

    connection = module.connect(*args, **kwargs)
    try:
        yield connection
    finally:
        if save_on_close:
            connection.commit()
        connection.close()
