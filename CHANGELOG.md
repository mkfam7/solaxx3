# Changelog

## 2.0.0

Full rewrite for production readiness. **Breaking changes** from the
original single-file version:

- Package restructured: `solaxx3.py` / `utils.py` / `solax_registers_info.py`
  -> `solaxx3/{client,utils,registers,decoding,models,exceptions}.py`.
- `SolaxRegistersInfo` (a ~3500-line hardcoded class) replaced by
  `RegisterRepository`, backed by `solaxx3/data/registers.json`. A
  deprecated shim (`solaxx3.legacy.SolaxRegistersInfo`) is provided for one
  release to ease migration -- it emits a `DeprecationWarning`.
- `SolaxX3.read()` now returns a `RegisterReading` `NamedTuple`
  (`.value` / `.unit`) instead of a plain tuple. Existing
  `value, unit = client.read(name)` call sites still work unchanged.
- `SolaxX3.read_all_registers()` now raises `SolaxConnectionError` if
  called before `connect()` succeeds, instead of silently reading nothing.
- Reading now raises typed exceptions (`UnknownRegisterError`,
  `RegistersNotLoadedError`, `RegisterReadError`) instead of letting
  raw `KeyError` / `IndexError` / `AttributeError` propagate from
  internal state.
- Modbus error responses (`response.isError()`) are now checked; previously
  a failed read would raise an opaque `AttributeError` when the code tried
  to access `.registers` on an error response.
- Added `SolaxX3.disconnect()` and context-manager support
  (`with SolaxX3(...) as inverter:`). Previously there was no way to close
  the serial connection.
- The number of registers read per block is now derived from the register
  catalog instead of a hardcoded `range(4)` / 100-register assumption.
- `pymodbus` version detection is now cached at construction time instead
  of being recomputed on every single read.
- **Retry with backoff on transient reads.** Each register block read is
  now retried (default: 3 attempts, exponential backoff starting at 0.2s)
  before raising `RegisterReadError`. Configurable via
  `SolaxX3(max_retries=..., retry_backoff_seconds=...)`.
- **Sanity-range validation on decoded values.** `RegisterInfo` gained
  optional `min_value`/`max_value` fields. When set, `read()` raises the
  new `RegisterValueOutOfRangeError` if a decoded value falls outside
  them -- catches corrupted reads that would otherwise look like valid
  data. Applied to six registers in the bundled catalog as examples
  (`grid_voltage`, `grid_current`, `grid_frequency`,
  `radiator_temperature`, `pv_voltage_1`, `pv_voltage_2`); add more as
  needed. Disable globally with `SolaxX3(validate_ranges=False)`.
- **JSON schema validation at catalog load time.** `registers.json` (or
  any custom catalog file) is now validated against a schema
  (`solaxx3/schema.py`) before being parsed into `RegisterInfo` objects.
  A malformed catalog raises `CatalogValidationError` listing every
  problem found, not just the first.
- **Fixed incorrect pymodbus `slave`/`device_id` keyword detection for
  most versions.** The previous logic only used `slave=` for pymodbus
  `3.9.x` exactly and `device_id=` for every other version -- but pymodbus
  actually used `slave=` for the entire `3.0`-`3.9` series and only
  renamed it to `device_id=` in `3.10.0`
  ([pymodbus PR #2600](https://github.com/pymodbus-dev/pymodbus/pull/2600)).
  Any installation on pymodbus 3.0-3.8 (a very commonly pinned range) was
  silently sending the wrong keyword and every read would fail. Detection
  now uses the correct `< 3.10` / `>= 3.10` boundary, plus a runtime
  self-correcting fallback: if pymodbus still rejects the guessed keyword
  with a `TypeError`, the client switches to the other name automatically
  and remembers it for the rest of its lifetime -- so an unusual version
  string or a future pymodbus rename degrades to one extra call instead of
  a broken client.
- **Moved to a `src/` layout**: `solaxx3/` -> `src/solaxx3/`. `tests/` now
  imports the package from an installed copy rather than the working
  directory, which is what `pyproject.toml`'s
  `pip install -e ".[dev]"` has always set you up for -- this just makes
  it the only way imports resolve, catching packaging mistakes (e.g. a
  data file missing from `package-data`) that a flat layout can hide.
  `[tool.setuptools.packages.find]` now points at `where = ["src"]`.
  If you're working from a checkout, run `pip install -e ".[dev]"` once
  before running `pytest` or importing `solaxx3` anywhere.

