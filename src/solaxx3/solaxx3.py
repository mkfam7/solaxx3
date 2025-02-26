"""Class loading and storing data from the inverter."""

from datetime import datetime
from struct import unpack
from typing import Dict, Iterable, List, Literal, Tuple, Union

from pymodbus.client import ModbusSerialClient

from .solax_registers_info import FIELD_VALUES, FIELDS, SolaxRegistersInfo
from .utils import join_msb_lsb, twos_complement

REGISTER_VALUE = Union[float, str, datetime]
REGISTER_INFO = Dict[FIELDS, FIELD_VALUES]


class SolaxX3:
    """
    Class interacting with values from the inverter.
    Initialization parameters:
        - port (default: /dev/ttyUSB0 )
        - baudrate: Bits per second (default: 115,200 )
        - timeout: Timeout for a request, in seconds. (default: 3)
        - parity: 'E'ven, 'O'dd, 'N'one (default: N)
        - stopbits: Number of stop bits 0-2 (default: 1)
        - bytesize: Number of bits per byte (7 or 8) (default: 8)
    """

    connected: bool = False
    READ_BLOCK_LENGTH = 100

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        timeout: int = 3,
        parity: Literal["E", "O", "N"] = "N",
        stopbits: Literal[0, 1, 2] = 1,
        bytesize: Literal[7, 8] = 8,
    ) -> None:
        self._input_registers_values: List[int] = []
        self._holding_registers_values: List[int] = []

        self.client: ModbusSerialClient = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
        )

    def connect(self) -> bool:
        """Connect to the inverter and return if it was successful."""

        self.connected: bool = self.client.connect()
        return self.connected

    def _get_unsigned_16(self, value_type: str, address: int) -> int:
        if value_type == "input":
            return self._input_registers_values[address]
        return self._holding_registers_values[address]

    def _read_register_range(
        self, value_type: str, address: int, count: int = 1
    ) -> list:
        if value_type == "input":
            return self._input_registers_values[address : address + count]
        return self._holding_registers_values[address : address + count]

    def _read_format_register_value(
        self, register_info: REGISTER_INFO
    ) -> REGISTER_VALUE:
        """Read the values from a register based on length and sign

        Parameters:
            register_info:dict  - dictionary with register definition fields
        """

        if self._is_register_type_integer(register_info):
            value = self._get_integer_value(register_info)
            value = value / register_info["si_adj"]

        elif self._is_register_type_string(register_info):
            value = self._get_string_value(register_info)

        else:
            value = self._get_datetime_value(register_info)

        return value

    def _get_datetime_value(self, register_info: REGISTER_INFO) -> datetime:
        register_type = register_info["register_type"]

        sec, minute, hr, day, mon, year = self._read_register_range(
            register_type, register_info["address"], register_info["data_length"]
        )
        inverter_datetime = f"{year:02}-{mon:02}-{day:02} {hr:02}:{minute:02}:{sec:02}"
        value = datetime.strptime(inverter_datetime, "%y-%m-%d %H:%M:%S")
        return value

    def _is_register_type_datetime(self, register_info: REGISTER_INFO) -> bool:
        return "datetime" in register_info["data_format"]

    def _get_string_value(self, register_info: REGISTER_INFO) -> str:
        characters: List[str] = []
        register_type: Literal["input", "holding"] = register_info["register_type"]
        block = self._read_register_range(
            register_type, register_info["address"], register_info["data_length"]
        )

        for i in range(register_info["data_length"]):
            first_byte, second_byte = unpack("BB", int.to_bytes(block[i], 2, "little"))
            if not second_byte == 0x0:
                characters.append(chr(second_byte))
            if not first_byte == 0x0:
                characters.append(chr(first_byte))

        return "".join(characters)

    def _is_register_type_string(self, register_info: REGISTER_INFO) -> bool:
        return "varchar" in register_info["data_format"]

    def _get_integer_value(self, register_info: REGISTER_INFO) -> int:
        register_type = register_info["register_type"]
        val = 0

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

    def _is_register_type_integer(self, register_info: REGISTER_INFO) -> bool:
        return "int" in register_info["data_format"]

    def _read_register_value(
        self, register_info: REGISTER_INFO
    ) -> Tuple[REGISTER_VALUE, str]:
        """Read the values from a register based on length and sign.

        Parameters:
            :param register_info: dictionary with register definition fields
            :return: Tuple containing the value and data unit
        """

        val = self._read_format_register_value(register_info)
        return (val, register_info["data_unit"])

    def read(self, name: str) -> Tuple[REGISTER_VALUE, str]:
        """Retrieve the value for the register with the provided name"""

        registers = SolaxRegistersInfo()
        register_info = registers.get_register_info(name)
        value_data_unit = self._read_register_value(register_info)
        return value_data_unit

    def list_register_names(self) -> list:
        """Return all registers defined in register info."""

        r = SolaxRegistersInfo()
        return r.list_register_names()

    def read_all_registers(self) -> None:
        """Read all register values from inverter."""

        self._input_registers_values: List[int] = []
        self._holding_registers_values: List[int] = []

        self._read_input_registers()
        self._read_holding_registers()

    def _read_holding_registers(self):
        for count in range(4):
            address: int = count * self.READ_BLOCK_LENGTH

            values: Iterable = self.client.read_holding_registers(
                address=address, count=self.READ_BLOCK_LENGTH, slave=1
            ).registers
            self._holding_registers_values.extend(values)

    def _read_input_registers(self):
        for count in range(4):
            address: int = count * self.READ_BLOCK_LENGTH

            values: Iterable = self.client.read_input_registers(
                address=address, count=self.READ_BLOCK_LENGTH, slave=1
            ).registers
            self._input_registers_values.extend(values)
