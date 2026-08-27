from datetime import datetime

import pytest

from solaxx3.decoding import decode_register_value
from solaxx3.exceptions import RegisterValueOutOfRangeError
from solaxx3.models import RegisterInfo


def make_register(**overrides) -> RegisterInfo:
    defaults = dict(
        name="test_register",
        address=0,
        register_type="input",
        data_format="uint16",
        data_length=1,
        signed=False,
        si_adj=1,
        data_unit="V",
        description="Test register",
    )
    defaults.update(overrides)
    return RegisterInfo(**defaults)


def test_decodes_unsigned_16_bit_integer():
    register = make_register(data_format="uint16", si_adj=10)
    assert decode_register_value(register, [1234]) == 123.4


def test_decodes_signed_16_bit_negative_integer():
    register = make_register(data_format="int16", signed=True, si_adj=1)
    assert decode_register_value(register, [0xFFFF]) == -1


def test_decodes_32_bit_integer_from_two_words():
    register = make_register(data_format="uint32", data_length=2, si_adj=1)
    # msb=raw_words[1], lsb=raw_words[0], per the inverter's word order
    assert decode_register_value(register, [0x0002, 0x0001]) == 0x00010002


def test_decodes_string_from_ascii_pairs():
    register = make_register(data_format="varchar", data_length=2, si_adj=1, data_unit="N/A")
    # 'A' = 0x41, 'B' = 0x42 packed high/low byte per word
    word_ab = (ord("A") << 8) | ord("B")
    word_cd = (ord("C") << 8) | ord("D")
    assert decode_register_value(register, [word_ab, word_cd]) == "ABCD"

def test_decodes_datetime():
    register = make_register(
        data_format="datetime", data_length=6, si_adj=1, data_unit="N/A"
    )
    # sec, minute, hr, day, mon, year
    raw = [5, 30, 14, 23, 8, 26]
    assert decode_register_value(register, raw) == datetime(2026, 8, 23, 14, 30, 5)


def test_raises_on_invalid_datetime():
    register = make_register(
        data_format="datetime", data_length=6, si_adj=1, data_unit="N/A"
    )
    raw = [0, 0, 99, 40, 13, 26]  # month 13 is invalid
    with pytest.raises(ValueError):
        decode_register_value(register, raw)


def test_raises_when_not_enough_raw_words_provided():
    register = make_register(data_format="uint32", data_length=2)
    with pytest.raises(ValueError):
        decode_register_value(register, [1])


class TestRangeValidation:
    def test_value_within_bounds_does_not_raise(self):
        register = make_register(si_adj=10, min_value=0, max_value=300)
        # raw 2200 / si_adj 10 = 220.0, within [0, 300]
        assert decode_register_value(register, [2200]) == 220.0

    def test_value_below_minimum_raises(self):
        register = make_register(si_adj=1, min_value=100, max_value=300)
        with pytest.raises(RegisterValueOutOfRangeError) as exc_info:
            decode_register_value(register, [50])
        assert exc_info.value.name == "test_register"
        assert exc_info.value.value == 50
        assert exc_info.value.minimum == 100
        assert exc_info.value.maximum == 300

    def test_value_above_maximum_raises(self):
        register = make_register(si_adj=1, min_value=0, max_value=300)
        with pytest.raises(RegisterValueOutOfRangeError):
            decode_register_value(register, [301])

    def test_no_bounds_configured_never_raises(self):
        register = make_register(si_adj=1)  # min_value/max_value default to None
        assert decode_register_value(register, [999999]) == 999999

    def test_validate_range_false_skips_the_check(self):
        register = make_register(si_adj=1, min_value=0, max_value=10)
        # would raise if validated; validate_range=False disables the check
        assert decode_register_value(register, [999], validate_range=False) == 999

    def test_range_check_does_not_apply_to_strings(self):
        register = make_register(
            data_format="varchar", data_length=1, si_adj=1, min_value=0, max_value=10
        )
        word = (ord("A") << 8) | 0
        assert decode_register_value(register, [word]) == "A"
