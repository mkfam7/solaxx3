"""Low-level binary helpers for interpreting raw Modbus register words."""

from __future__ import annotations


def join_msb_lsb(msb: int, lsb: int) -> int:
    """Join two 16-bit register words into a single 32-bit integer.

    Args:
        msb: the most-significant 16-bit word (0-65535).
        lsb: the least-significant 16-bit word (0-65535).

    Example:
        >>> join_msb_lsb(0x0001, 0x0002)
        65538
    """

    if not 0 <= msb <= 0xFFFF:
        raise ValueError(f"msb must fit in 16 bits, got {msb}")
    if not 0 <= lsb <= 0xFFFF:
        raise ValueError(f"lsb must fit in 16 bits, got {lsb}")

    return (msb << 16) | lsb


def twos_complement(number: int, bits: int) -> int:
    """Interpret ``number`` as a signed two's-complement integer of ``bits`` width.

    Example:
        >>> twos_complement(0xFFFF, 16)
        -1
        >>> twos_complement(0x7FFF, 16)
        32767
    """

    if bits <= 0:
        raise ValueError(f"bits must be positive, got {bits}")

    # if the sign bit is set (e.g. for 8 bits: values 128-255), the number
    # represents a negative value.
    if (number & (1 << (bits - 1))) != 0:
        number = number - (1 << bits)

    return number
