from typing import Any
from pymodbus.client.sync import ModbusSerialClient
from datetime import date, datetime, timedelta
from struct import *
from solaxx3.registers import SolaxRegistersInfo
from time import sleep


class SolaxX3G4:
    connected: bool = False

    def __init__(
        self,
        method="rtu",
        port="/dev/ttyUSB0",
        baudrate=115200,
        timeout=3,
        parity="N",
        stopbits=1,
        bytesize=8,
    ) -> None:
        self._registers_values_list = []

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

    def __join_msb_lsb(self, msb: int, lsb: int) -> int:
        return (msb << 16) | lsb

    def _unsigned16(self, type: str, addr: int, count: int = 1, unit: int = 1) -> int:
        if type == "input":
            return self.client.read_input_registers(
                address=addr, count=count, unit=unit
            ).getRegister(0)
        elif type == "holding":
            return self.client.read_holding_registers(
                address=addr, count=count, unit=unit
            ).getRegister(0)

    def _readRawRegVar(
        self, type: str, addr: int, count: int = 1, unit: int = 1
    ) -> int:
        if type == "input":
            return self.client.read_input_registers(
                address=addr, count=count, unit=unit
            )
        elif type == "holding":
            return self.client.read_holding_registers(
                address=addr, count=count, unit=unit
            )

    def _twos_comp(self, number: int, bits: int) -> int:
        """
        Compute the 2's complement of the int value val
        """

        # if sign bit is set e.g., 8bit: 128-255
        if (number & (1 << (bits - 1))) != 0:

            # compute negative value
            number = number - (1 << bits)

        return number

    def __read_register(self, register_type: str, register_info: dict) -> Any:
        """Read the values from a register based on length and sign

        Parameters:

            register_info:dict  - dictionary with register definition fields
        """

        if "int" in register_info["data_format"]:
            if register_info["data_length"] == 1:
                val = self._unsigned16(register_type, register_info["address"])

            if register_info["data_length"] == 2:
                val = self.__join_msb_lsb(
                    self._unsigned16(register_type, register_info["address"] + 1),
                    self._unsigned16(register_type, register_info["address"]),
                )

            if register_info["signed"]:
                val = self._twos_comp(val, register_info["data_length"] * 16)

            val = val / register_info["si_adj"]

        elif "varchar" in register_info["data_format"]:
            block = self._readRawRegVar(
                register_type, register_info["address"], register_info["data_length"]
            )
            sn = []
            for i in range(register_info["data_length"]):
                first_byte, second_byte = unpack(
                    "BB", int.to_bytes(block.getRegister(i), 2, "little")
                )
                if not second_byte == 0x0:
                    sn.append(chr(second_byte))
                if not first_byte == 0x0:
                    sn.append(chr(first_byte))
            val = "".join(sn)

        elif "datetime" in register_info["data_format"]:
            block = self._readRawRegVar(
                register_type, register_info["address"], register_info["data_length"]
            )
            sec = block.getRegister(0)
            min = block.getRegister(1)
            hr = block.getRegister(2)
            day = block.getRegister(3)
            mon = block.getRegister(4)
            year = block.getRegister(5)

            inverter_datetime = (
                f"{(year+2000):02}-{mon:02}-{day:02} {hr:02}:{min:02}:{sec:02}"
            )
            val = datetime.strptime(inverter_datetime, "%Y-%m-%d %H:%M:%S")

        return val

    def read_register(self, register_info: dict) -> tuple:
        """Read the values from a register based on length and sign

        Parameters:

            register_info:dict  - dictionary with register definition fields
        """

        val = self.__read_register(register_info["register_type"], register_info)

        if not "data_unit" in register_info:
            return (val, "N/A")

        return (val, register_info["data_unit"])

    def read(self, name: str):
        """Retrieve the value for the register with the provided name"""

        r = SolaxRegistersInfo()

        register_info = r.get_register_info(name)
        value = self.read_register(register_info)

        return value

    def list_register_names(self):
        r = SolaxRegistersInfo()
        return r.list_register_names()

    def read_all_registers(self) -> None:
        self._registers_values_list = []

        read_block_length = 100
        for i in range(3):
            address = i * read_block_length
            values_list = self.client.read_input_registers(
                address=address, count=read_block_length, unit=1
            ).registers
            self._registers_values_list.extend(values_list)

            # this is mandatory for the safety of the invertor (according to manufacturer' instructions)
            sleep(1)
