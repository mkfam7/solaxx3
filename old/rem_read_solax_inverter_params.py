from pymodbus.client.sync import ModbusSerialClient
from datetime import date, datetime, timedelta
from struct import *
from registers import SolaxRegistersInfo


class SolaxX3G4:
    connected: bool = False

    def __init__(self) -> None:
        self.client = ModbusSerialClient(
            method="rtu",
            port="/dev/ttyUSB0",
            baudrate=115200,
            timeout=3,
            parity="N",
            stopbits=1,
            bytesize=8,
        )

    def connect(self) -> bool:
        self.connected = self.client.connect()
        return self.connected

    def __join_msb_lsb(self, msb, lsb):
        return (msb << 16) | lsb

    def __unsigned16(self, type: str, addr: int, count: int = 1, unit: int = 1) -> int:
        if type == "input":
            return self.client.read_input_registers(
                address=addr, count=count, unit=unit
            ).getRegister(0)
        elif type == "holding":
            return self.client.read_holding_registers(
                address=addr, count=count, unit=unit
            ).getRegister(0)

    def _twos_comp(self, number: int, bits: int) -> int:
        """
        Compute the 2's complement of the int value val
        """

        # if sign bit is set e.g., 8bit: 128-255
        if (number & (1 << (bits - 1))) != 0:

            # compute negative value
            number = number - (1 << bits)

        return number

    def __read_input_register(self, register_info: dict) -> tuple:
        """Read the values from a register based on length and sign

        Parameters:

            register_info:dict  - dictionary with register definition fields
        """

        if register_info["data_length"] == 1:
            val = self.__unsigned16("input", register_info["address"])

        if register_info["data_length"] == 2:
            val = self.__join_msb_lsb(
                self.__unsigned16("input", register_info["address"] + 1),
                self.__unsigned16("input", register_info["address"]),
            )

        if register_info["signed"]:
            val = self._twos_comp(val, register_info["data_length"] * 16)

        return val

    def __read_holding_register(self, register_info: dict) -> tuple:
        block = self.client.read_holding_registers(
            address=register_info["address"],
            count=register_info["data_length"],
            unit=1,
        )

        sn = []
        for i in range(register_info["data_length"]):
            first_byte, second_byte = unpack(
                "BB", int.to_bytes(block.getRegister(i), 2, "little")
            )
            sn.append(chr(second_byte))
            sn.append(chr(first_byte))
        val = "".join(sn)

        return val

    def read_register(self, register_info: dict) -> tuple:
        """Read the values from a register based on length and sign

        Parameters:

            register_info:dict  - dictionary with register definition fields
        """

        if register_info["register_type"] == "input":
            val = self.__read_input_register(register_info)

        elif register_info["register_type"] == "holding":
            val = self.__read_holding_register(register_info)

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


s = SolaxX3G4()


if s.connect():
    # s.load_input_registers()
    # s.load_holding_registers()
    print(s.read("battery_capacity"))
    print(s.read("serial_number"))
    print(s.list_register_names())


else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()
