import sys
from os import environ
from pathlib import Path
from unittest import TestCase

from tests.mock_packages.mysql.connection import Connection
from tests.mock_packages.mysql.cursor import Cursor

environ["MYSQL_DB_USERNAME"] = ""
environ["MYSQL_DB_HOST_IP"] = ""
environ["MYSQL_DB_PASSWORD"] = ""
environ["MYSQL_DB_DATABASE"] = ""
current: Path = Path().resolve()
paths_to_extend = [current / "tests" / "mock_packages", current / "src"]
for path in paths_to_extend:
    path_as_string = str(path)
    if path_as_string not in sys.path:
        sys.path.insert(0, path_as_string)

from database import read_and_save


class MysqlConnectionLeakageTests(TestCase):
    """Tests to see if the class leaves any connections open after its processes."""

    def _open_connections(self):
        return Connection(consider_open=False).open_connections

    def setUp(self) -> None:
        """Set up the data after each test case."""

        Cursor(raise_err=False)._raise_error = False
        Cursor(raise_err=False)._raise_error_in_init = False
        Connection().open_connections = 0

    def test_bulk_transfer_without_error(self):
        """Test if `bulk_transfer` leaves any hanging connections in normal operations."""

        for _ in range(3):
            read_and_save.bulk_save()

        self.assertEqual(self._open_connections(), 0)

    def test_bulk_transfer_with_error_in_cursor_init(self):
        """Test if `bulk_transfer` leaves any hanging connections with errors when instantiating
        cursor."""

        Cursor()._raise_error_in_init = True
        for _ in range(3):
            try:
                read_and_save.bulk_save()
            except:
                pass

        self.assertEqual(self._open_connections(), 0)

    def test_bulk_transfer_with_error_in_cursor(self):
        """Test if `bulk_transfer` leaves any hanging connections with errors when executing
        a query in the cursor."""

        Cursor()._raise_error = True
        for _ in range(3):
            try:
                read_and_save.bulk_save()
            except:
                pass

        self.assertEqual(self._open_connections(), 0)
