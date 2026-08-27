"""Client for reading register values from a Solax X3 inverter over Modbus."""

from __future__ import annotations

import logging
import time
from typing import Any, List, Literal, Optional

from pymodbus import __version__ as pymodbus_version
from pymodbus.client import ModbusSerialClient

from .decoding import decode_register_value
from .exceptions import (
    RegisterReadError,
    RegistersNotLoadedError,
    SolaxConnectionError,
)
from .models import RegisterReading, RegisterType
from .registers import RegisterRepository, default_repository

logger = logging.getLogger(__name__)

_MAX_REGISTERS_PER_REQUEST = 100


class SolaxX3:
    """Reads register values from a Solax X3 inverter over Modbus RTU.

    Can be used as a context manager, which connects on entry and
    disconnects on exit::

        with SolaxX3(port="/dev/ttyUSB0") as inverter:
            inverter.read_all_registers()
            voltage, unit = inverter.read("grid_voltage")

    Args:
        port: serial device path (default: ``/dev/ttyUSB0``).
        baudrate: bits per second (default: 115200).
        timeout: timeout for a request, in seconds (default: 3).
        parity: ``"E"``ven, ``"O"``dd, or ``"N"``one (default: ``"N"``).
        stopbits: number of stop bits, 0-2 (default: 1).
        bytesize: number of bits per byte, 7 or 8 (default: 8).
        device_id: Modbus unit/slave id of the inverter (default: 1).
        register_repository: source of register definitions. Defaults to
            the catalog bundled with this package — override only if you
            need a custom or partial register set.
        max_retries: number of attempts for each block read before giving
            up and raising :class:`RegisterReadError` (default: 3). Guards
            against transient RS485/serial glitches, which are common on
            these links.
        retry_backoff_seconds: base delay between retry attempts; doubles
            after each attempt (exponential backoff), e.g. with the
            default 0.2 the delays are 0.2s, 0.4s, ... (default: 0.2).
        validate_ranges: if True (default), raise
            :class:`RegisterValueOutOfRangeError` when a decoded value
            falls outside the sanity bounds declared for that register (if
            any). Set to False to disable this check globally.
    """

    def __init__(
        self,
        port: str = "/dev/ttyUSB0",
        baudrate: int = 115200,
        timeout: int = 3,
        parity: Literal["E", "O", "N"] = "N",
        stopbits: Literal[0, 1, 2] = 1,
        bytesize: Literal[7, 8] = 8,
        device_id: int = 1,
        register_repository: Optional[RegisterRepository] = None,
        max_retries: int = 3,
        retry_backoff_seconds: float = 0.2,
        validate_ranges: bool = True,
    ) -> None:
        if max_retries < 1:
            raise ValueError(f"max_retries must be >= 1, got {max_retries}")

        self._device_id = device_id
        self._registers = register_repository or default_repository()
        self._slave_param_name = _guess_slave_param_name(pymodbus_version)
        self._max_retries = max_retries
        self._retry_backoff_seconds = retry_backoff_seconds
        self._validate_ranges = validate_ranges

        self._input_registers_values: List[int] = []
        self._holding_registers_values: List[int] = []

        self._connected = False

        self.client = ModbusSerialClient(
            port=port,
            baudrate=baudrate,
            timeout=timeout,
            parity=parity,
            stopbits=stopbits,
            bytesize=bytesize,
        )

    @property
    def connected(self) -> bool:
        return self._connected

    def __enter__(self) -> SolaxX3:
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.disconnect()

    def connect(self) -> bool:
        """Connect to the inverter. Returns whether the connection succeeded."""

        try:
            self._connected = self.client.connect()
        except Exception:
            logger.exception("Failed to connect to inverter on %s", self.client)
            self._connected = False

        if not self._connected:
            logger.error("Could not establish a connection to the inverter")

        return self._connected

    def disconnect(self) -> None:
        """Close the serial connection to the inverter, if open."""

        self.client.close()
        self._connected = False

    def read_all_registers(self) -> None:
        """Read every known input and holding register from the inverter.

        Must be called (at least once) before :meth:`read`. Raises
        :class:`RegisterReadError` if either read fails.
        """

        if not self._connected:
            raise SolaxConnectionError(
                "Not connected to the inverter. Call connect() first."
            )

        self._input_registers_values = self._read_register_block(
            "input", self.client.read_input_registers
        )
        self._holding_registers_values = self._read_register_block(
            "holding", self.client.read_holding_registers
        )

    def read(self, name: str) -> RegisterReading:
        """Return the decoded value and unit for the register named ``name``.

        Raises:
            UnknownRegisterError: if ``name`` isn't a known register.
            RegistersNotLoadedError: if :meth:`read_all_registers` hasn't
                been called yet.
            RegisterValueOutOfRangeError: if range validation is enabled
                and the decoded value falls outside the register's
                declared sanity bounds.
        """

        register_info = self._registers.get(name)
        raw_words = self._read_register_range(
            register_info.register_type, register_info.address, register_info.data_length
        )
        value = decode_register_value(
            register_info, raw_words, validate_range=self._validate_ranges
        )
        return RegisterReading(value=value, unit=register_info.data_unit)

    def list_register_names(self) -> List[str]:
        """Return the names of every register this client can read."""

        return self._registers.list_names()

    def _read_register_block(self, register_type: RegisterType, read_fn) -> List[int]:
        register_count = self._registers.max_register_count(register_type)
        values: List[int] = []
        address = 0

        while address < register_count:
            block_size = min(_MAX_REGISTERS_PER_REQUEST, register_count - address)
            response = self._read_block_with_retry(
                read_fn, register_type, address, block_size
            )
            values.extend(response.registers)
            address += block_size

        return values

    def _read_block_with_retry(
        self, read_fn, register_type: RegisterType, address: int, block_size: int
    ) -> Any:
        """Read one block, retrying transient failures with exponential backoff.

        A "transient failure" is either an exception raised by pymodbus
        itself (e.g. a serial timeout) or a Modbus error response
        (``response.isError()``) — both are common on noisy RS485 links and
        usually succeed on the next attempt. Raises
        :class:`RegisterReadError` only once every attempt has failed.
        """

        last_error: Any = None

        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._call_read(read_fn, address, block_size)
            except Exception as exc:  # pymodbus raises various exception types
                last_error = exc
                logger.warning(
                    "Attempt %d/%d: reading %s registers [%d:%d] raised %s",
                    attempt,
                    self._max_retries,
                    register_type,
                    address,
                    address + block_size,
                    exc,
                )
            else:
                if response is not None and not response.isError():
                    return response
                last_error = response
                logger.warning(
                    "Attempt %d/%d: reading %s registers [%d:%d] returned "
                    "an error response: %s",
                    attempt,
                    self._max_retries,
                    register_type,
                    address,
                    address + block_size,
                    response,
                )

            if attempt < self._max_retries:
                delay = self._retry_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(delay)

        raise RegisterReadError(
            f"Failed to read {register_type} registers "
            f"[{address}:{address + block_size}] after {self._max_retries} "
            f"attempt(s): {last_error}"
        )

    def _call_read(self, read_fn, address: int, block_size: int) -> Any:
        """Call ``read_fn``, self-correcting the slave/device_id keyword.

        The keyword name guessed in ``__init__`` from the pymodbus version
        string might be wrong (unusual version string, a vendored fork, a
        future rename pymodbus makes). If pymodbus rejects it with a
        ``TypeError`` naming that keyword, this flips to the other name,
        remembers it for every subsequent call on this client, and retries
        once immediately — so a wrong guess costs one extra call the first
        time, not a permanently broken client.
        """

        try:
            return read_fn(
                address=address,
                count=block_size,
                **{self._slave_param_name: self._device_id},
            )
        except TypeError as exc:
            if self._slave_param_name not in str(exc):
                raise  # an unrelated TypeError — not ours to handle

            corrected_name = (
                "slave" if self._slave_param_name == "device_id" else "device_id"
            )
            logger.warning(
                "pymodbus rejected the '%s' keyword (%s); this pymodbus "
                "version apparently expects '%s' instead — switching to it "
                "for the rest of this client's lifetime",
                self._slave_param_name,
                exc,
                corrected_name,
            )
            self._slave_param_name = corrected_name
            return read_fn(
                address=address,
                count=block_size,
                **{self._slave_param_name: self._device_id},
            )

    def _read_register_range(
        self, register_type: RegisterType, address: int, count: int
    ) -> List[int]:
        values = (
            self._input_registers_values
            if register_type == "input"
            else self._holding_registers_values
        )

        if not values:
            raise RegistersNotLoadedError()

        if address + count > len(values):
            raise RegisterReadError(
                f"{register_type} register range [{address}:{address + count}] "
                f"is outside the {len(values)} registers currently loaded. "
                "Call read_all_registers() again if the inverter's register "
                "map may have changed."
            )

        return values[address : address + count]


def _guess_slave_param_name(version_string: str) -> str:
    """Best-effort guess of the Modbus unit-id keyword from a pymodbus version.

    pymodbus's history for this keyword:
        < 3.0      "unit="
        3.0 - 3.9  "slave="
        3.10+      "device_id="  (renamed in pymodbus PR #2600)

    This package requires pymodbus>=3.0 (see pyproject.toml), so only the
    "slave" / "device_id" split is handled here. This is a *guess* from the
    version string — :meth:`SolaxX3._call_read` corrects it at runtime if
    it turns out to be wrong, so an unusual version string (a pre-release,
    a vendored fork, a future rename) degrades to "one extra retry" rather
    than a hard failure.
    """

    try:
        major, minor, *_ = (int(part) for part in version_string.split("."))
    except ValueError:
        logger.warning(
            "Could not parse pymodbus version %r; assuming a recent version "
            "and using the 'device_id' parameter name (will self-correct if "
            "that's wrong)",
            version_string,
        )
        return "device_id"

    return "slave" if (major, minor) < (3, 10) else "device_id"
