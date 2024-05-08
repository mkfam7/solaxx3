"""SolaxX3 utils module performing binary operations."""


def join_msb_lsb(msb: int, lsb: int) -> int:
    """Join two 16-bit registers into a 32-bit register."""

    return (msb << 16) | lsb


def twos_complement(number: int, bits: int) -> int:
    """Compute the 2's complement of the provided integer."""

    # if sign bit is set e.g., 8bit: 128-255
    if (number & (1 << (bits - 1))) != 0:
        # compute negative value
        number = number - (1 << bits)

    return number
