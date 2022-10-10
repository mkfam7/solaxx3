from pymodbus.client.sync import ModbusSerialClient
from datetime import date, datetime, timedelta
from struct import *
import mysql.connector
from solaxx3.rs485 import SolaxX3G4


s = SolaxX3G4(port="/dev/ttyUSB0", baudrate=115200)


if s.connect():
    # print(s.read("battery_capacity"))
    # print(s.read("serial_number"))
    # print(s.list_register_names())
    # print(s.read("firmware_version_dsp"))
    # print(s.read("temperature_battery"))

    # uploadTime = s.read("rtc_datetime")[0]

    bb = s.read_all_registers()
    # print(f"ok: {s.read('consumption_energy_today')}")

    def join_msb_lsb(msb: int, lsb: int) -> int:
        return (msb << 16) | lsb

    def twos_comp(number: int, bits: int) -> int:
        """
        Compute the 2's complement of the int value val
        """

        # if sign bit is set e.g., 8bit: 128-255
        if (number & (1 << (bits - 1))) != 0:

            # compute negative value
            number = number - (1 << bits)

        return number

    aa = join_msb_lsb(bb[0x9B], bb[0x9A])

    # print(bb[0x11D])

    print(twos_comp(aa, 32))


else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()
