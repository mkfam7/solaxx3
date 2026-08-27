"""solaxx3 — read register values from a Solax X3 inverter over Modbus RTU."""

from .client import SolaxX3
from .exceptions import (
    CatalogValidationError,
    RegisterReadError,
    RegistersNotLoadedError,
    RegisterValueOutOfRangeError,
    SolaxConnectionError,
    SolaxX3Error,
    UnknownRegisterError,
)
from .models import RegisterInfo, RegisterReading
from .registers import RegisterRepository, default_repository

__version__ = "2.0.0"

__all__ = [
    "SolaxX3",
    "SolaxX3Error",
    "SolaxConnectionError",
    "UnknownRegisterError",
    "RegistersNotLoadedError",
    "RegisterReadError",
    "RegisterValueOutOfRangeError",
    "CatalogValidationError",
    "RegisterInfo",
    "RegisterReading",
    "RegisterRepository",
    "default_repository",
]
