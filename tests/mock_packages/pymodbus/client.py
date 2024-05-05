from collections import namedtuple

from .registers_output import raw_holding_register_values, raw_input_register_values
from .utils import getnext

Registers = namedtuple("Registers", ["registers"])


class ModbusSerialClient:
    def __init__(self, *args, **kwargs) -> None:
        self._holding_registers_gen = getnext(raw_holding_register_values)
        self._input_registers_gen = getnext(raw_input_register_values)

    def connect(self):
        return True

    def read_holding_registers(self, count, *args, **kwargs):
        return Registers([next(self._holding_registers_gen) for _ in range(count)])

    def read_input_registers(self, count, *args, **kwargs):
        return Registers([next(self._input_registers_gen) for _ in range(count)])
