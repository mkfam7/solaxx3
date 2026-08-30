"""Typed data models shared across the package."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, NamedTuple, Union

RegisterType = Literal["input", "holding"]
DataFormat = Literal["uint16", "int16", "uint32", "int32", "varchar", "datetime"]

RegisterValue = Union[float, str, datetime]


@dataclass(frozen=True)
class RegisterInfo:
    """Immutable description of a single Modbus register.

    Replaces the previous loosely-typed ``Dict[str, Union[int, str]]``
    representation with a validated, self-documenting structure.
    """

    name: str
    address: int
    register_type: RegisterType
    data_format: DataFormat
    data_length: int
    signed: bool
    si_adj: float
    data_unit: str
    description: str
    # Optional sanity bounds applied to the *decoded* value (after si_adj),
    # not the raw register word. None means "no bound configured" — most
    # registers don't have one. Only meaningful for integer registers.
    min_value: float | None = None
    max_value: float | None = None

    def __post_init__(self) -> None:
        if self.address < 0:
            raise ValueError(f"{self.name}: address must be >= 0, got {self.address}")
        if self.data_length < 1:
            raise ValueError(
                f"{self.name}: data_length must be >= 1, got {self.data_length}"
            )
        if self.si_adj == 0:
            raise ValueError(f"{self.name}: si_adj must not be zero")
        if (
            self.min_value is not None
            and self.max_value is not None
            and self.min_value > self.max_value
        ):
            raise ValueError(
                f"{self.name}: min_value ({self.min_value}) is greater than "
                f"max_value ({self.max_value})"
            )

    @property
    def is_integer(self) -> bool:
        return "int" in self.data_format

    @property
    def is_string(self) -> bool:
        return self.data_format == "varchar"

    @property
    def is_datetime(self) -> bool:
        return self.data_format == "datetime"

    @property
    def end_address(self) -> int:
        """Address one past the last register word this value occupies."""

        return self.address + self.data_length

    @classmethod
    def from_dict(cls, name: str, data: dict) -> RegisterInfo:
        try:
            return cls(
                name=name,
                address=data["address"],
                register_type=data["register_type"],
                data_format=data["data_format"],
                data_length=data["data_length"],
                signed=data["signed"],
                si_adj=data["si_adj"],
                data_unit=data["data_unit"],
                description=data["description"],
                min_value=data.get("min_value"),
                max_value=data.get("max_value"),
            )
        except KeyError as exc:
            raise ValueError(f"Register {name!r} is missing field {exc}") from exc


class RegisterReading(NamedTuple):
    """Result of reading a single register.

    A ``NamedTuple`` so existing call sites that unpack the previous
    ``Tuple[value, unit]`` return value (``value, unit = client.read(...)``)
    keep working, while new code can use ``.value`` / ``.unit``.
    """

    value: RegisterValue
    unit: str
