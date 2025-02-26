"""Module to test solaxx3."""

import sys
import unittest
from pathlib import Path

from src.solaxx3 import solaxx3
from tests.final_result import (
    altered_holding_register_values,
    altered_input_register_values,
)

import_path = Path().resolve() / "tests" / "mock_packages"
if str(import_path) not in sys.path:
    sys.path.insert(0, str(import_path))


class Solaxx3Tests(unittest.TestCase):
    """Tests for SolaxX3."""

    def test_connection(self):
        """Test if SolaxX3 connected."""

        s = solaxx3.SolaxX3()
        s.connect()
        self.assertEqual(s.connected, True)

    def test_format_registers(self):
        """Test if the module correctly formats raw register values."""

        result = []
        s = solaxx3.SolaxX3()
        s.read_all_registers()

        regs = solaxx3.SolaxRegistersInfo().list_register_names()
        for reg in regs:
            result.append(s.read(reg)[0])

        self.assertEqual(
            result, altered_input_register_values + altered_holding_register_values
        )

    def test_are_registers_identical(self):
        """Test if holding registers' values are not equal to input registers' values."""

        s = solaxx3.SolaxX3()
        s.read_all_registers()
        self.assertFalse(s._holding_registers_values == s._input_registers_values)
