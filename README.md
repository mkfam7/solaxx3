# solaxx3

[![PyPI version](https://img.shields.io/pypi/v/solaxx3.svg)](https://pypi.org/project/solaxx3/)
[![Python versions](https://img.shields.io/pypi/pyversions/solaxx3.svg)](https://pypi.org/project/solaxx3/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Build badge](https://github.com/mkfam7/solaxx3/actions/workflows/python-package.yml/badge.svg)

Read register values from a **Solax X3** series inverter over **Modbus RTU** (serial/RS485).

`solaxx3` wraps [pymodbus](https://pypi.org/project/pymodbus/) with a catalog of
~350 known Solax X3 registers, so you can read a value by name - `"grid_voltage"`,
`"bms_user_soc"`, `"pv_voltage_1"` - instead of tracking raw register addresses and
decoding logic yourself.

## Features

- **Read by name** - a bundled JSON catalog maps ~350 register names to address,
  data type, scaling, and unit; decoding (signed integers, 32-bit values, strings,
  datetimes) is handled for you.
- **Customizable catalog** - bring your own register definitions (a different
  firmware revision, a subset, extra registers) as a JSON file.

## Installation

```bash
pip install solaxx3
```

Requires Python 3.9+ and [pymodbus](https://pypi.org/project/pymodbus/) 3.0+
(installed automatically as a dependency).

## Quick start

```python
from solaxx3 import SolaxX3

with SolaxX3(port="/dev/ttyUSB0", baudrate=115200) as inverter:
    inverter.read_all_registers()

    voltage, unit = inverter.read("grid_voltage")
    print(f"Grid voltage: {voltage} {unit}")

    for name in inverter.list_register_names():
        reading = inverter.read(name)
        print(f"{name}: {reading.value} {reading.unit}")
```

Without the context manager:

```python
inverter = SolaxX3(port="/dev/ttyUSB0")
if not inverter.connect():
    raise RuntimeError("Could not connect to inverter")

try:
    inverter.read_all_registers()
    reading = inverter.read("grid_voltage")
finally:
    inverter.disconnect()
```

## Configuration

```python
SolaxX3(
    port="/dev/ttyUSB0",  # serial device
    baudrate=115200,  # baudrate value configured on inverter
    timeout=3,
    device_id=1,  # Modbus unit/slave id of the inverter
    max_retries=3,  # attempts per block read
    retry_backoff_seconds=0.2,  # base delay; doubles each retry
    validate_ranges=True,  # enforce sanity bounds on decoded values
)
```

## Error handling

All errors raised by this package subclass `solaxx3.SolaxX3Error`, so you can
catch broadly or handle specific cases:

```python
from solaxx3 import SolaxX3, UnknownRegisterError, RegisterReadError

with SolaxX3() as inverter:
    inverter.read_all_registers()
    try:
        reading = inverter.read("grid_voltage")
    except UnknownRegisterError:
        ...  # no register with that name in the catalog
    except RegisterReadError:
        ...  # inverter didn't respond after retries
```

Other exceptions: `SolaxConnectionError`, `RegistersNotLoadedError`,
`RegisterValueOutOfRangeError`, `CatalogValidationError`.

## Custom register catalogs

To read from a different or partial register set (e.g. a different firmware
revision), supply your own catalog file:

```python
from solaxx3 import SolaxX3, RegisterRepository

repo = RegisterRepository.from_json_file("my_registers.json")
inverter = SolaxX3(register_repository=repo)
```

## Links

- [Source code](https://github.com/mkfam7/solaxx3)
- [Issue tracker](https://github.com/mkfam7/solaxx3/issues)

## Development

Contributions welcome. Clone the repository, `pip install -e ".[dev]"`, and
run `pytest`. See [DEVELOPMENT.md](https://github.com/mkfam7/solaxx3/blob/main/DEVELOPMENT.md)
for the register catalog field reference, Modbus domain notes, and other
details that aren't obvious from the code alone, and
[CHANGELOG.md](https://github.com/mkfam7/solaxx3/blob/main/CHANGELOG.md)
for release history.

## License

MIT
