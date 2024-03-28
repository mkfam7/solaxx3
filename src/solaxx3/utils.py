def join_msb_lsb(msb: int, lsb: int) -> int:
    return (msb << 16) | lsb


def twos_complement(number: int, bits: int) -> int:
    """
    Compute the 2's complement of the int value val
    """

    # if sign bit is set e.g., 8bit: 128-255
    if (number & (1 << (bits - 1))) != 0:
        # compute negative value
        number = number - (1 << bits)

    return number
