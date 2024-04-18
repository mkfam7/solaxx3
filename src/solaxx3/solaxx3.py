from datetime import datetime
from struct import unpack
from typing import Any, Literal

from pymodbus.client import ModbusSerialClient

from .solax_registers_info import SolaxRegistersInfo
from .utils import join_msb_lsb, twos_complement


class SolaxX3:
    """
    Class interacting with values from the inverter.
    Initialization parameters:
        - method (default: rtu)
        - port (default: /dev/ttyUSB0 )
        - baudrate: Bits per second (default: 115,200 )
        - timeout: Timeout for a request, in seconds. (default: 3)
        - parity: 'E'ven, 'O'dd, 'N'one (default: N)
        - stopbits: Number of stop bits 0-2 (default: 1)
        - bytesize: Number of bits per byte (7 or 8) (default: 8)
    """

    connected: bool = False

    def __init__(
        self,
        method: str = "rtu",
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        timeout: int = 3,
        parity: Literal["E", "O", "N"] = "N",
        stopbits: Literal[0, 1, 2] = 1,
        bytesize: Literal[7, 8] = 8,
    ) -> None:
        self._input_registers_values = []
        self._holding_registers_values = []

        self.client = ModbusSerialClient(
            method=method,
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
        )

    def connect(self) -> bool:
        self.connected = self.client.connect()
        return self.connected

    def _get_unsigned_16(self, value_type: str, address: int) -> int:
        if value_type == "input":
            return self._input_registers_values[address]
        elif value_type == "holding":
            return self._holding_registers_values[address]

    def _read_register_range(
        self, value_type: str, address: int, count: int = 1
    ) -> list:
        if value_type == "input":
            return self._input_registers_values[address : address + count]
        elif value_type == "holding":
            return self._holding_registers_values[address : address + count]

    def _read_format_register_value(self, register_info: dict) -> Any:
        """Read the values from a register based on length and sign

        Parameters:
            register_info:dict  - dictionary with register definition fields
        """

        if self.is_register_type_integer(register_info):
            value = self._get_integer_value(register_info)
            value = value / register_info["si_adj"]

        elif self._is_register_type_string(register_info):
            value = self._get_string_value(register_info)

        elif self._is_register_type_datetime(register_info):
            value = self._get_datetime_value(register_info)

        return value

    def _get_datetime_value(self, register_info):
        register_type = register_info["register_type"]

        sec, min, hr, day, mon, year = self._read_register_range(
            register_type, register_info["address"], register_info["data_length"]
        )
        # modified !!!
        inverter_datetime = f"{year:02}-{mon:02}-{day:02} {hr:02}:{min:02}:{sec:02}"
        value = datetime.strptime(inverter_datetime, "%y-%m-%d %H:%M:%S")
        return value

    def _is_register_type_datetime(self, register_info):
        return "datetime" in register_info["data_format"]

    def _get_string_value(self, register_info):
        register_type = register_info["register_type"]

        block = self._read_register_range(
            register_type, register_info["address"], register_info["data_length"]
        )
        sn = []
        for i in range(register_info["data_length"]):
            first_byte, second_byte = unpack("BB", int.to_bytes(block[i], 2, "little"))
            if not second_byte == 0x0:
                sn.append(chr(second_byte))
            if not first_byte == 0x0:
                sn.append(chr(first_byte))

        return "".join(sn)

    def _is_register_type_string(self, register_info):
        return "varchar" in register_info["data_format"]

    def _get_integer_value(self, register_info):
        register_type = register_info["register_type"]

        if register_info["data_length"] == 1:
            val = self._get_unsigned_16(register_type, register_info["address"])

        if register_info["data_length"] == 2:
            val = join_msb_lsb(
                self._get_unsigned_16(register_type, register_info["address"] + 1),
                self._get_unsigned_16(register_type, register_info["address"]),
            )

        if register_info["signed"]:
            val = twos_complement(val, register_info["data_length"] * 16)
        return val

    def is_register_type_integer(self, register_info: dict[str, Any]) -> bool:
        return "int" in register_info["data_format"]

    def read_register_value(self, register_info: dict) -> tuple:
        """Read the values from a register based on length and sign.

        Parameters:
            :param register_info: dictionary with register definition fields
            :return: Tuple containing the value and data unit
        """

        val = self._read_format_register_value(register_info)
        return (val, register_info["data_unit"])

    def read(self, name: str):
        """Retrieve the value for the register with the provided name"""

        registers = SolaxRegistersInfo()

        register_info = registers.get_register_info(name)
        value_data_unit = self.read_register_value(register_info)

        return value_data_unit

    def list_register_names(self):
        r = SolaxRegistersInfo()
        return r.list_register_names()

    def read_all_registers(self) -> None:
        self._input_registers_values = []
        self._holding_registers_values = []

        READ_BLOCK_LENGTH = 100
        self._read_input_registers(READ_BLOCK_LENGTH)
        self._read_holding_registers(READ_BLOCK_LENGTH)

    def _read_holding_registers(self, READ_BLOCK_LENGTH):
        for count in range(4):
            address = count * READ_BLOCK_LENGTH
            values = self.client.read_holding_registers(
                address=address, count=READ_BLOCK_LENGTH, slave=1
            ).registers
            self._holding_registers_values.extend(values)

    def _read_input_registers(self, READ_BLOCK_LENGTH):
        for count in range(4):
            address = count * READ_BLOCK_LENGTH

            values = self.client.read_input_registers(
                address=address, count=READ_BLOCK_LENGTH, slave=1
            ).registers
            self._input_registers_values.extend(values)
