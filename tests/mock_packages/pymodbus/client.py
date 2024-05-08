"""Class to mimick `pymodbus.client`. It is used when running the tests."""

from collections import namedtuple

from .registers_output import raw_holding_register_values, raw_input_register_values
from .utils import getnext

Registers = namedtuple("Registers", ["registers"])


class ModbusSerialClient:
    """Class mimicking `pymodbus.client.ModbusSerialClient`."""

    def __init__(self, *_, **__) -> None:
        self._holding_registers_gen = getnext(raw_holding_register_values)
        self._input_registers_gen = getnext(raw_input_register_values)

    def connect(self):
        """Mimick connecting the inverter and return the success code."""

        return True

    def read_holding_registers(self, count, *_, **__):
        """Read holding register values from inverter."""

        return Registers([next(self._holding_registers_gen) for _ in range(count)])

    def read_input_registers(self, count, *_, **__):
        """Read input register values from inverter."""
        return Registers([next(self._input_registers_gen) for _ in range(count)])
