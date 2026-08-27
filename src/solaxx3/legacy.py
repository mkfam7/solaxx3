"""Backward-compatibility shim for the old ``SolaxRegistersInfo`` API.

Deprecated: use :func:`solaxx3.registers.default_repository` and
:class:`solaxx3.registers.RegisterRepository` instead. This module exists
only so that code written against the previous version of this package
doesn't break immediately; it will be removed in a future release.
"""

from __future__ import annotations

import warnings
from typing import Dict, List, Literal, Union

from .registers import default_repository

FIELDS = Literal[
    "address",
    "register_type",
    "data_format",
    "si_adj",
    "signed",
    "data_unit",
    "data_length",
    "description",
]
FIELD_VALUES = Union[int, str]


class SolaxRegistersInfo:
    """Deprecated. Use :func:`solaxx3.registers.default_repository`."""

    def __init__(self) -> None:
        warnings.warn(
            "SolaxRegistersInfo is deprecated; use "
            "solaxx3.registers.default_repository() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        self._repository = default_repository()

    def get_register_info(self, name: str) -> Dict[FIELDS, FIELD_VALUES]:
        info = self._repository.get(name)
        return {
            "address": info.address,
            "register_type": info.register_type,
            "data_format": info.data_format,
            "si_adj": info.si_adj,
            "signed": info.signed,
            "data_unit": info.data_unit,
            "data_length": info.data_length,
            "description": info.description,
        }

    def list_register_names(self) -> List[str]:
        return self._repository.list_names()

    def list_holding_registers(self) -> List[str]:
        return self._repository.list_names_by_type("holding")

    def list_input_registers(self) -> List[str]:
        return self._repository.list_names_by_type("input")
