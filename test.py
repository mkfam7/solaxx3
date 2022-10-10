from pymodbus.client.sync import ModbusSerialClient
from datetime import date, datetime, timedelta
from struct import *
import mysql.connector
from solaxx3.rs485 import SolaxX3G4


s = SolaxX3G4(port="/dev/ttyUSB0", baudrate=115200)


if s.connect():
    s.read_all_registers()

    print(f"ok: {s.read('temperature_battery')}")


else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()
