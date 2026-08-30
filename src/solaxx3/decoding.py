"""Decode raw 16-bit register words into typed Python values.

This is deliberately free of any Modbus/serial I/O: it only knows how to
turn a list of raw register ints into the value a :class:`RegisterInfo`
describes. Keeping it pure makes it trivial to unit test without a real
(or mocked) inverter connection.
"""

from __future__ import annotations

from datetime import datetime
from struct import unpack

from .exceptions import RegisterValueOutOfRangeError
from .models import RegisterInfo, RegisterValue
from .utils import join_msb_lsb, twos_complement


def decode_register_value(
    register_info: RegisterInfo, raw_words: list[int], validate_range: bool = True
) -> RegisterValue:
    """Decode ``raw_words`` (one entry per 16-bit register) per ``register_info``.

    Args:
        register_info: description of the register being decoded.
        raw_words: the raw register words, starting at ``register_info.address``,
            with at least ``register_info.data_length`` entries.
        validate_range: if True (default) and ``register_info`` declares
            ``min_value``/``max_value``, raise :class:`RegisterValueOutOfRangeError`
            when the decoded value falls outside them. Only applies to
            numeric (integer) registers.
    """

    if len(raw_words) < register_info.data_length:
        raise ValueError(
            f"{register_info.name}: expected {register_info.data_length} "
            f"register word(s), got {len(raw_words)}"
        )

    if register_info.is_integer:
        value = _decode_integer(register_info, raw_words)
        if validate_range:
            _check_range(register_info, value)
        return value
    if register_info.is_string:
        return _decode_string(register_info, raw_words)
    return _decode_datetime(register_info, raw_words)


def _check_range(register_info: RegisterInfo, value: float) -> None:
    below_minimum = (
        register_info.min_value is not None and value < register_info.min_value
    )
    above_maximum = (
        register_info.max_value is not None and value > register_info.max_value
    )
    if below_minimum or above_maximum:
        raise RegisterValueOutOfRangeError(
            register_info.name, value, register_info.min_value, register_info.max_value
        )


def _decode_integer(register_info: RegisterInfo, raw_words: list[int]) -> float:
    if register_info.data_length == 1:
        value = raw_words[0]
    elif register_info.data_length == 2:
        value = join_msb_lsb(raw_words[1], raw_words[0])
    else:
        raise ValueError(
            f"{register_info.name}: unsupported integer data_length "
            f"{register_info.data_length}"
        )

    if register_info.signed:
        value = twos_complement(value, register_info.data_length * 16)

    return value / register_info.si_adj


def _decode_string(register_info: RegisterInfo, raw_words: list[int]) -> str:
    characters: list[str] = []

    for word in raw_words[: register_info.data_length]:
        low_byte, high_byte = unpack("BB", int.to_bytes(word, 2, "little"))
        if high_byte != 0x0:
            characters.append(chr(high_byte))
        if low_byte != 0x0:
            characters.append(chr(low_byte))

    return "".join(characters)


def _decode_datetime(register_info: RegisterInfo, raw_words: list[int]) -> datetime:
    sec, minute, hr, day, mon, year = raw_words[: register_info.data_length]
    text = f"{year:02}-{mon:02}-{day:02} {hr:02}:{minute:02}:{sec:02}"
    try:
        return datetime.strptime(text, "%y-%m-%d %H:%M:%S")
    except ValueError as exc:
        raise ValueError(
            f"{register_info.name}: inverter returned an invalid datetime {text!r}"
        ) from exc
