from pymodbus.client.sync import ModbusSerialClient
from datetime import date
from struct import *
from pymodbus.payload import BinaryPayloadBuilder


def unsigned16(result, addr):
    return result.getRegister(addr)


def join_msb_lsb(msb, lsb):
    return (msb << 16) | lsb


def twos_comp(val, bits):
    """compute the 2's complement of int value val"""

    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val = val - (1 << bits)  # compute negative value
    return val  # return positive value as is


client = ModbusSerialClient(
    method="rtu",
    port="/dev/ttyUSB0",
    # baudrate=9600,
    baudrate=115200,
    timeout=3,
    parity="N",
    stopbits=1,
    bytesize=8,
)

if client.connect():  # Trying for connect to Modbus Server/Slave
    """Reading from a holding register with the below content."""

    offset_size = 100
    max_offset_count = 2

    block = client.read_holding_registers(address=0, count=7, unit=1)

    block = client.read_input_registers(address=0, count=125, unit=1)

    print(block.registers(0x46))

    exit()

    sn = []
    for i in range(7):
        first, second = unpack("BB", int.to_bytes(block.getRegister(i), 2, "little"))
        # print(block.getRegister(i))
        sn.append(chr(second))
        sn.append(chr(first))
        # H34T15H9022043

    print("".join(sn))


else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()


# print("ok")
