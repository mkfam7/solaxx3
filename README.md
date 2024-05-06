![Build badge](https://github.com/mkfam7/solaxx3/actions/workflows/python-package.yml/badge.svg)



# solax-x3
####  Read in real-time all parameters provided by Solax X3 solar inverter via its Modbus S-485 serial interface.

<br />

## Prerequisites

* Solax X3 inverter
* Modbus RS-485 serial adapter/interface
* [Modbus cable](https://github.com/mkfam7/solaxx3/blob/main/diagrams/rs485_cable.png)
* python version >= 3.8
* This python module

## Installation

```
pip install solaxx3
```  

## Usage


```
from solaxx3.solaxx3 import SolaxX3

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


```

Project Link: [https://github.com/mkfam7/solaxx3](https://github.com/mkfam7/solaxx3)



