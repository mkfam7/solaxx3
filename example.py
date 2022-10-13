from solaxx3.rs485 import SolaxX3

# adjust the serial port and baud rate as necessary
s = SolaxX3(port="/dev/ttyUSB0", baudrate=115200)

if s.connect():
    s.read_all_registers()

    available_stats = s.list_register_names()
    for stat in available_stats:
        print(stat)

    battery_temperature = s.read("temperature_battery")
    print(f"\n\nBattery temperature: {s.read('temperature_battery')}")


else:
    print("Cannot connect to the Modbus Server/Slave")
    exit()
