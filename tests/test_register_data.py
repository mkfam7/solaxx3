"""
Test scenarios:
    Report any of the following anomalies:
        1. Not valid dictionary syntax [done]
        2. Dictionary key duplicates [done]
        3. "address" duplicates
        4. The value field has different keys than: [done]
            * address
            * register_type
            * data_format
            * si_adj
            * signed
            * data_unit
            * data_length
            * description
        5. "dataformat" starts with 'uint' but "signed" is different than "False"
        6. "dataformat" starts with 'int' but "signed" is different than "True"
        7. If "data_format" contains "int" in the name,
            "data_length" != <the number inside "data_format"> / 16 or 1 if no number is found
            in "data_length"
        8. "data_unit" is not one of following:
            {%, A, C, Hx, KWh, N/A, V, VA, Var, W, Wh, hour, second}
            Note: values are case sensitive
        9. "register_type" is different than {input, holding}
            Note: no values are case sensitive
        10. the key name contains "volt" but the "data_unit" is different than "V"
        11. the key name contains "current" but the "data_unit" is different than "A"
        12. "address" overlapping
"""

import re
import sys
import unittest
from itertools import filterfalse
from pathlib import Path

from src.solaxx3.solax_registers_info import SolaxRegistersInfo

import_path = Path().resolve() / "tests" / "mock_packages"
if str(import_path) not in sys.path:
    sys.path.insert(0, str(import_path))

REGISTER_FILE = "src/solaxx3/solax_registers_info.py"


class RegisterTests(unittest.TestCase):
    """Tests for SolaxRegistersInfo."""

    registers = SolaxRegistersInfo._registers

    def test_tc1_valid_dictionary(self):
        """Prints an error if `registers` is a dictionary."""

        self.assertIsInstance(self.registers, dict)

    def test_tc2_duplicate_keys(self):
        """Prints an error if 'registers' has any duplicate keys."""

        PATTERN = r"""
        "(?P<key>.*?)"   # The key of the dictionary
        \s*:             # colon
        \s*{             # start of value
        """
        regex = re.compile(PATTERN, re.VERBOSE)

        with open(REGISTER_FILE, "r", encoding="utf-8") as dictionary:
            list_keys = []

            for line_number, line in filterfalse(
                lambda x: x[1].lstrip().startswith("#"), enumerate(dictionary, start=1)
            ):
                re_match = regex.search(line)

                if re_match is not None:
                    key = re_match.group("key")
                    self.assertNotIn(key, list_keys, f"line={line_number}")
                    list_keys.append(key)

    def test_tc4_correct_value_field(self):
        """Prints an error if the keys do not have the following keys:
        - address, register_type, data_format, si_adj, signed, data_unit, data_length,
        description"""

        VALID_SUBKEYS = [
            "address",
            "data_format",
            "data_length",
            "data_unit",
            "description",
            "register_type",
            "si_adj",
            "signed",
        ]

        for register, register_value in self.registers.items():
            self.assertListEqual(
                sorted(list(register_value.keys())), VALID_SUBKEYS, f"dict={register!r}"
            )

    def test_tc5_correctly_unsigned(self):
        """Prints an error if subkey `data_format` starts with `uint` but `signed` is
        different than False."""

        for register, register_value in self.registers.items():
            self.assertFalse(
                register_value["data_format"].startswith("uint")
                and register_value["signed"] is not False,
                f"not correctly signed: dict='{register}'",
            )

    def test_tc6_correctly_signed(self):
        """Prints an error if subkey `data_format` starts with 'int' but `signed`
        is different than True."""

        for register, register_value in self.registers.items():
            self.assertFalse(
                register_value["data_format"].startswith("int")
                and register_value["signed"] is not True,
                f"not correctly signed: dict='{register}'",
            )

    def test_tc7_correct_data_length(self):
        """Prints an error if 'data_format' does not match 'data_length'."""

        PATTERN = r"int(?P<bits>\d+)"
        regex = re.compile(PATTERN)

        for register, register_value in self.registers.items():
            match = regex.search(register_value["data_format"])

            if match:
                bits = int(match.group("bits"))
                self.assertEqual(
                    bits / 16, register_value["data_length"], f"dict={register!r}"
                )

    def test_tc8_correct_data_unit_value(self):
        """Prints an error if `data_unit` is not %, C, Hz, KWh, N/A, V, VA, Var,
        W, Wh, hour, second."""

        POSSIBLE_DATA_UNITS = (
            "min",
            "bps",
            "%",
            "A",
            "C",
            "Hz",
            "KWh",
            "N/A",
            "V",
            "VA",
            "Var",
            "W",
            "Wh",
            "hour",
            "second",
        )

        for register, register_value in self.registers.items():
            self.assertGreater(
                len(register_value["data_unit"]),
                0,
                f"empty 'data_unit': dict={register!r}",
            )
            self.assertIn(
                register_value["data_unit"],
                POSSIBLE_DATA_UNITS,
                f"invalid data_unit: '{register_value['data_unit']}'; 'dict='{register}'",
            )

    def test_tc9_correct_register_type(self):
        """Prints an error if `register_type` is not 'input' or 'holding'."""

        POSSIBLE_REGISTER_TYPES = ("input", "holding")

        for register, register_value in self.registers.items():
            self.assertIn(
                register_value["register_type"],
                POSSIBLE_REGISTER_TYPES,
                f"dict='{register}'",
            )

    def test_tc10_correct_data_unit_with_volt(self):
        """Prints an error if the key contains 'volt' but `data_unit` is differrent
        than 'V'."""

        for register, register_value in self.registers.items():
            self.assertFalse(
                "volt" in register
                and register_value["data_unit"] != "V"
                and "percent" not in register
                and "ratio" not in register,
                f"'data_unit' does not match name: dict={register!r}",
            )

    def test_tc11_correct_data_unit_with_current(self):
        """Prints an error if the key contains 'current' but `data_unit` is
        differrent than 'A'."""

        for register, register_value in self.registers.items():
            self.assertFalse(
                "current" in register and register_value["data_unit"] != "A",
                f"'data_unit' does not match name: dict='{register}'",
            )

    def test_tc12_correct_addresses(self):
        """Prints an error if there is any address overlapping."""

        holding_addresses: list = []
        input_addresses: list = []

        for register, register_value in self.registers.items():
            addresses = (
                holding_addresses
                if register_value["register_type"] == "holding"
                else input_addresses
            )
            data_length = register_value["data_length"]

            for x in range(data_length):
                address = register_value["address"] + x
                self.assertNotIn(address, addresses, f"dict={register!r}")
                addresses.append(address)

    def test_tc13_subkey_duplicates(self):
        """Prints an error if there are any subkey duplicates."""

        PATTERN = r"""
        "(?P<subkey>.*?)"  # dictionary subkey
        \s*:            # colon
        \s*?[^[]+$      # value different than a dict
        """

        regex = re.compile(PATTERN, re.VERBOSE)

        with open(REGISTER_FILE, "r", encoding="utf-8") as dictionary:
            subkeys = []

            for line_number, line in filterfalse(
                lambda x: x[1].lstrip().startswith("#"), enumerate(dictionary, start=1)
            ):
                match = regex.search(line)

                if match:
                    subkey = match.group("subkey")

                    self.assertNotIn(subkey, subkeys, f"line={line_number}")
                    subkeys.append(subkey)
                else:
                    subkeys.clear()


if __name__ == "__main__":
    unittest.main()
