"""Exceptions raised by the solaxx3 package.

Having a dedicated hierarchy lets callers catch ``SolaxX3Error`` for any
package-specific failure, or a more specific subclass when they need to
react differently (e.g. retry on :class:`RegisterReadError` but fail fast
on :class:`UnknownRegisterError`).
"""

from __future__ import annotations

from typing import List, Optional


class SolaxX3Error(Exception):
    """Base class for all errors raised by this package."""


class SolaxConnectionError(SolaxX3Error):
    """Raised when the connection to the inverter cannot be established."""


class UnknownRegisterError(SolaxX3Error, KeyError):
    """Raised when a register name is not present in the register catalog.

    Inherits from ``KeyError`` too, so existing code that only expects a
    ``KeyError`` from a dict-like lookup keeps working.
    """

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(f"Unknown register: {name!r}")


class RegistersNotLoadedError(SolaxX3Error):
    """Raised when a register is read before ``read_all_registers`` ran."""

    def __init__(self) -> None:
        super().__init__(
            "No register data has been read yet. Call read_all_registers() "
            "before reading individual register values."
        )


class RegisterReadError(SolaxX3Error):
    """Raised when a Modbus read request to the inverter fails.

    Raised only after retries (see ``SolaxX3(max_retries=...)``) have been
    exhausted — a single transient failure does not raise this.
    """


class CatalogValidationError(SolaxX3Error):
    """Raised when a register catalog JSON file fails schema validation.

    Carries every problem found in the file (not just the first one), since
    catalog files are hand-edited and it's much faster to fix all the
    mistakes in one pass than to fix-and-reload repeatedly.
    """

    def __init__(self, errors: List[str]) -> None:
        self.errors = errors
        details = "\n".join(f"  - {error}" for error in errors)
        super().__init__(f"Register catalog failed validation:\n{details}")


class RegisterValueOutOfRangeError(SolaxX3Error):
    """Raised when a decoded value falls outside its register's sanity range.

    This signals the *reading* is implausible (e.g. a corrupted register or
    a decoding bug) — not a communication failure, so it is not retried the
    way :class:`RegisterReadError` is.
    """

    def __init__(
        self,
        name: str,
        value: float,
        minimum: Optional[float],
        maximum: Optional[float],
    ) -> None:
        self.name = name
        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        super().__init__(
            f"{name}: decoded value {value} is outside the expected range "
            f"[{minimum}, {maximum}] — the reading may be corrupted"
        )
