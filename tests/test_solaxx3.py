import sys
import unittest
from pathlib import Path

from src.solaxx3 import solaxx3
from tests.final_result import (
    altered_holding_register_values,
    altered_input_register_values,
)

import_path = Path().resolve() / "tests" / "mock_packages"
if sys.path[-1] != str(import_path):
    sys.path.append(str(import_path))


class Solaxx3Tests(unittest.TestCase):
    def test_connection(self):
        s = solaxx3.SolaxX3()
        s.connect()
        self.assertEqual(s.connected, True)

    def test_format_registers(self):
        r = []
        s = solaxx3.SolaxX3()
        s.read_all_registers()

        regs = solaxx3.SolaxRegistersInfo().list_register_names()
        for reg in regs:
            r.append(s.read(reg)[0])

        self.assertEqual(
            r, altered_input_register_values + altered_holding_register_values
        )

    def test_are_registers_identical(self):
        s = solaxx3.SolaxX3()
        s.read_all_registers()
        self.assertFalse(s._holding_registers_values == s._input_registers_values)
