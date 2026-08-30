# Development Guide

This document describes the internal design and behavior of `solaxx3`module.

---

## Table of contents

- [1. Data flow: register to value](#1-data-flow-register-to-value)
- [2. Register catalog field reference](#2-register-catalog-field-reference)
- [3. Data formats](#3-data-formats)
  - [`uint16` / `int16`](#uint16--int16)
  - [`uint32` / `int32`](#uint32--int32)
  - [`varchar`](#varchar)
  - [`datetime`](#datetime)
- [4. Project structure](#4-project-structure)
- [5. Implementation details](#5-implementation-details)
- [6. Adding a new register](#6-adding-a-new-register)
- [7. Adding a new data format](#7-adding-a-new-data-format)
- [8. Testing](#8-testing)

---

## 1. Data flow: register to value

```
inverter.read("grid_voltage")
    │
    ├─ 1. RegisterRepository.get("grid_voltage")        (registers.py)
    │      -> looks up the RegisterInfo: address=0, register_type="input",
    │        data_format="uint16", si_adj=10, signed=False, ...
    │
    ├─ 2. _read_register_range("input", address=0, count=1)  (client.py)
    │      -> slices the raw ints already fetched by read_all_registers()
    │        out of self._input_registers_values
    │
    ├─ 3. decode_register_value(register_info, raw_words)     (decoding.py)
    │      -> interprets the raw 16-bit int(s) per data_format/signed/si_adj
    │      -> optionally checks min_value/max_value
    │
    └─ 4. RegisterReading(value=220.0, unit="V")               (models.py)
           -> returned to the caller
```

Steps 1 and 4 are lookups and data shaping. Step 2 is the only step that
touches state fetched from the inverter, via `read_all_registers()` in
`client.py`, which performs the Modbus I/O with retries. Step 3 performs
decoding with no I/O.

---

## 2. Register catalog field reference

Every entry in `src/solaxx3/data/registers.json` has this shape:

```json
"grid_voltage": {
  "address": 0,
  "register_type": "input",
  "data_format": "uint16",
  "si_adj": 10,
  "signed": false,
  "data_unit": "V",
  "data_length": 1,
  "description": "Grid voltage",
  "min_value": 80,
  "max_value": 300
}
```

| Field | Meaning | Notes |
| --- | --- | --- |
| **`address`** | Where this value starts in the inverter's register map (0-based, within its `register_type`'s address space). | Input and holding registers are separate address spaces - `address: 0` for an input register and `address: 0` for a holding register are two different physical locations. Taken directly from the inverter manufacturer's Modbus protocol document. |
| **`register_type`** | `"input"` or `"holding"` - which Modbus address space `address` refers to. | Determines whether the client uses function code `0x04` (input, read-only) or `0x03` (holding, read/write) to fetch it. Which category a given value belongs to is decided by the manufacturer and is not inferable from the value itself. |
| **`data_format`** | One of `uint16`, `int16`, `uint32`, `int32`, `varchar`, `datetime`. Describes the shape of the data. | The `int`/`uint` naming does not by itself control sign decoding. See [section 5](#5-implementation-details). |
| **`si_adj`** | The scaling factor to divide the raw integer by, to get the value in `data_unit`. | Modbus registers only hold integers, so manufacturers preserve decimal precision by scaling: e.g. grid voltage transmitted as `2200` with `si_adj: 10` means `220.0 V`; a current transmitted in milliamps with `si_adj: 1000` converts to amps. The scale must be verified against the manufacturer's Modbus documentation. |
| **`signed`** | Whether the raw integer is interpreted as two's-complement signed. | This field controls sign handling during decoding (see [section 5](#5-implementation-details)). An incorrect value causes negative readings (e.g. battery discharge current) to decode as large positive numbers. |
| **`data_unit`** | The unit string after scaling: `"V"`, `"A"`, `"Hz"`, `"°C"`, `"%"`, `"Wh"`, etc. | Metadata for display only; has no effect on decoding. |
| **`data_length`** | Number of consecutive 16-bit registers this value occupies. | `1` for `uint16`/`int16`; `2` for `uint32`/`int32`; for `varchar`, the number of registers (each holds 2 ASCII characters, see [section 3](#3-data-formats)); `6` for `datetime` (one register per field: sec, minute, hour, day, month, year). An incorrect value truncates strings/datetime fields or misaligns subsequent registers when offsets are computed manually. |
| **`description`** | Human-readable explanation of what this register represents. | Free text, sourced from the manufacturer's documentation where possible. |
| **`min_value`** / **`max_value`** *(optional)* | Sanity bounds checked against the decoded value (after `si_adj` is applied), used to catch corrupted reads. | Not a substitute for real grid-code or hardware-spec limits - deliberately generous tripwires, not certified operating ranges. Only a small number of registers currently have these set. An unset bound is never checked. |

---

## 3. Data formats

### `uint16` / `int16`

One register: `value = raw_words[0]`. If `signed` is `true`, two's
complement is applied over 16 bits before scaling (`utils.twos_complement`).

### `uint32` / `int32`

Two registers combine into one 32-bit value via `utils.join_msb_lsb`. Word
order: the register at the lower address holds the least-significant word;
the register at the higher address holds the most-significant word.

```python
# raw_words[0] = register at `address`       -> low 16 bits
# raw_words[1] = register at `address + 1`   -> high 16 bits
value = join_msb_lsb(msb=raw_words[1], lsb=raw_words[0])
```

Example: if the register at `address` reads `0x0002` and the register at
`address + 1` reads `0x0001`, the combined 32-bit value is `0x00010002`,
not `0x00020001`. This is Solax's convention; other manufacturers commonly
use the opposite order, so it must be verified per device family if this
package is adapted for a different inverter line.

If `signed` is `true`, two's complement is applied over the full 32 bits
(`data_length * 16`) after joining, then the result is scaled by `si_adj`.

### `varchar`

Each register packs two ASCII characters, high byte first:

```python
low_byte, high_byte = unpack("BB", int.to_bytes(word, 2, "little"))
# high_byte decodes to the first character, low_byte to the second
```

A null byte (`0x00`) in either position is skipped rather than appended,
so a string shorter than `data_length * 2` characters (e.g. a device name
padded with zeros) decodes without embedded null characters.

### `datetime`

Each of the six registers holds one whole field value, not packed bytes:

```python
sec, minute, hr, day, mon, year = raw_words[:6]
```

`year` is a two-digit value (Solax's convention), interpreted via
`datetime.strptime(..., "%y-%m-%d %H:%M:%S")`, which Python resolves to
the 2000s (`26` -> `2026`). This assumption breaks for dates past 2099.

---

## 4. Project structure

```
src/solaxx3/
├── __init__.py           Public API surface -- what "from solaxx3 import X" exposes.
├── client.py              SolaxX3 -- Modbus I/O: connect, read (with retry/backoff), disconnect.
├── decoding.py            Pure functions: raw register words -> typed Python value.
├── models.py              RegisterInfo, RegisterReading -- the typed data shapes.
├── registers.py           RegisterRepository -- loads, validates, and serves the catalog.
├── schema.py              Validates registers.json's structure at load time.
├── exceptions.py          Every error this package can raise.
├── utils.py               join_msb_lsb / twos_complement -- the low-level binary math.
└── data/
    └── registers.json     The register definitions (hand-editable JSON).
tests/
    └── test_*.py          One test file per module above.
```

---

## 5. Implementation details

### `data_format`'s `int`/`uint` naming does not control sign decoding

`RegisterInfo.is_integer` is `"int" in self.data_format`, which is `True`
for all four numeric formats - `uint16` and `int16` both contain the
substring `"int"`, as do `uint32`/`int32`. `data_format` therefore only
distinguishes integer vs. string vs. datetime during decoding, not signed
vs. unsigned. **The `signed` field is what determines whether two's
complement is applied.**

Because decoding depends only on `signed`, a register's numeric
interpretation can be corrected or changed without updating its
`data_format` prefix - for example, a register originally cataloged as
`uint16` and later found to represent a signed quantity can be fixed by
setting `signed: true`, leaving `data_format` as `uint16`. The catalog
does not guarantee that `data_format` is kept consistent with `signed`
after such a change. A mismatch between the two should therefore not be
assumed to be an error; it should be checked against `signed` and the
manufacturer's documentation rather than against the `data_format` prefix
alone.

### The pymodbus `slave`/`device_id` keyword handling is two-layered

pymodbus renamed the client keyword for the device/unit id from `slave=`
to `device_id=` in version 3.10 (see `client.py`'s
`_guess_slave_param_name` docstring for exact version boundaries). Rather
than pin to one version, this package:

1. Guesses the correct keyword from the installed pymodbus version at
   construction time (`_guess_slave_param_name`).
2. Self-corrects at runtime if the guess is wrong - `_call_read` catches
   the resulting `TypeError`, switches to the other keyword, and retains
   the fix for the rest of that client's lifetime.

The runtime fallback covers pre-release version strings, vendored forks,
and any future rename, none of which the version guess alone can cover.

### Retries happen per register block, not per `read_all_registers()` call

`read_all_registers()` reads in blocks of up to 100 registers
(`_MAX_REGISTERS_PER_REQUEST`). If block 3 of 5 fails, only block 3 is
retried; blocks 1, 2, 4, 5 are not re-fetched. Worst case, a single call
can generate `num_blocks * max_retries` Modbus requests, not just
`max_retries`.

### The register catalog is a process-wide singleton by default

`default_repository()` is decorated with `@lru_cache(maxsize=1)` - the
bundled JSON is parsed once per process and shared by every `SolaxX3`
instance that does not pass its own `register_repository`. `RegisterInfo`
is `frozen=True`, so a `RegisterInfo` obtained from the shared repository
cannot be mutated by one caller in a way that would be visible to others.

### Adding a field to the JSON schema is two edits, not one

`schema.py`'s `REGISTER_ENTRY_SCHEMA` has `"additionalProperties": False`
- any key in `registers.json` not listed in `properties` fails validation
at load time. Adding a new field to `RegisterInfo` (in `models.py`) that
should be settable from JSON requires also adding it to
`REGISTER_ENTRY_SCHEMA["properties"]` in `schema.py`, or every catalog
file (including the bundled one, the moment the new field is used) fails
to load with `CatalogValidationError`.

### `src/` layout requires an editable install

The package lives under `src/solaxx3/`, with `tests/` as a sibling - not
`solaxx3/` next to `tests/`. `import solaxx3` fails on a bare checkout as
a result. `pip install -e ".[dev]"` must be run once before running tests
or importing the package interactively; see [section 8](#8-testing).

---

## 6. Adding a new register

1. Find the register's address, type, format, and scaling in the
   inverter's Modbus protocol documentation, or reverse-engineer against
   known-good readings if no documentation is available. If
   reverse-engineered, this should be noted in `description`, so the
   value is known to be unverified.
2. Add an entry to `src/solaxx3/data/registers.json`:

   ```json
   "battery_soc": {
     "address": 20,
     "register_type": "input",
     "data_format": "uint16",
     "si_adj": 1,
     "signed": false,
     "data_unit": "%",
     "data_length": 1,
     "description": "Battery state of charge"
   }
   ```

3. No code changes are required for the minimum case. Schema validation
   runs automatically on load; a malformed entry fails with a message
   naming the register and field.
4. `min_value`/`max_value` may optionally be added if a confident sanity
   range is known (see [section 2](#2-register-catalog-field-reference)).
   Bounds should remain generous, as they are a corruption tripwire, not
   a spec limit.
5. A test should be added or extended in `tests/test_decoding.py` if the
   register exercises a data format/edge case not already covered, and in
   `tests/test_registers.py` if it is a good example of a catalog-level
   property worth asserting on.

---

## 7. Adding a new data format

Extending the data format set beyond the current six requires three files
to change together:

1. **`models.py`** - add the new value to the `DataFormat` `Literal`, and,
   if it needs its own "is this format X" check (like `is_integer`/
   `is_string`/`is_datetime`), add a property for it.
2. **`schema.py`** - add the new value to
   `REGISTER_ENTRY_SCHEMA["properties"]["data_format"]["enum"]`, or every
   catalog entry using it fails schema validation.
3. **`decoding.py`** - add the decode logic, and a branch for it in
   `decode_register_value`.

Tests for the new format should be added in `test_decoding.py` (decode
logic, pure - no mocking needed) and `test_schema.py` (a valid entry using
the new format passes validation).

---

## 8. Testing

```bash
pip install -e ".[dev]"   # required once -- see the src/ layout note in section 5
pytest --cov=solaxx3
ruff check .
mypy src/solaxx3
```

One test file per module:

| Test file | Covers | Needs mocking? |
| --- | --- | --- |
| `test_utils.py` | `join_msb_lsb`, `twos_complement` | No |
| `test_models.py` | `RegisterInfo` validation | No |
| `test_schema.py` | The catalog validator, in isolation | No |
| `test_decoding.py` | Every data format, including range validation | No |
| `test_registers.py` | Catalog loading, lookup, schema enforcement | No |
| `test_client.py` | Connect/disconnect, retries, backoff timing, the slave/device_id self-correction, read errors | Yes - mocks `pymodbus.client.ModbusSerialClient` |

A test requiring `unittest.mock` outside `test_client.py` indicates that
the logic under test has acquired an I/O dependency it should not have.