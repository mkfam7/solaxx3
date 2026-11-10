# Changelog

## 2.0.0

Full rewrite for production readiness.

### Breaking changes

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

### Features

- Added `SolaxX3.disconnect()` and context-manager support (`with SolaxX3(...) as inverter:`). Previously there was no
  way to close the serial connection.
- **Retry with backoff on transient reads.** Each register block read is
  now retried (default: 3 attempts, exponential backoff starting at 0.2s)
  before raising `RegisterReadError`. Configurable via
  `SolaxX3(max_retries=..., retry_backoff_seconds=...)`.
- **Sanity-range validation on decoded values.** `RegisterInfo` gained
  optional `min_value`/`max_value` fields. When set, `read()` raises the
  new `RegisterValueOutOfRangeError` if a decoded value falls outside
  them -- catches corrupted reads that would otherwise look like valid
  data. Applied to six registers in the bundled catalog as examples (`grid_voltage`, `grid_current`, `grid_frequency`,
  `radiator_temperature`, `pv_voltage_1`, `pv_voltage_2`); add more as
  needed. Disable globally with `SolaxX3(validate_ranges=False)`.
- **JSON schema validation at catalog load time.** `registers.json` (or
  any custom catalog file) is now validated against a schema (`solaxx3/schema.py`) before being parsed into
  `RegisterInfo` objects.
  A malformed catalog raises `CatalogValidationError` listing every
  problem found, not just the first.
