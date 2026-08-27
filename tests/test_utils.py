import pytest

from solaxx3.utils import join_msb_lsb, twos_complement


class TestJoinMsbLsb:
    def test_joins_two_words_into_one_32_bit_value(self):
        assert join_msb_lsb(0x0001, 0x0002) == 0x00010002

    def test_zero_msb_returns_lsb(self):
        assert join_msb_lsb(0x0000, 0x1234) == 0x1234

    def test_rejects_msb_out_of_16_bit_range(self):
        with pytest.raises(ValueError):
            join_msb_lsb(0x10000, 0x0000)

    def test_rejects_lsb_out_of_16_bit_range(self):
        with pytest.raises(ValueError):
            join_msb_lsb(0x0000, -1)


class TestTwosComplement:
    def test_positive_value_within_range_is_unchanged(self):
        assert twos_complement(0x7FFF, 16) == 32767

    def test_sign_bit_set_returns_negative_value(self):
        assert twos_complement(0xFFFF, 16) == -1

    def test_zero_is_zero(self):
        assert twos_complement(0, 16) == 0

    def test_8_bit_negative_value(self):
        assert twos_complement(0b10000000, 8) == -128

    def test_rejects_non_positive_bit_width(self):
        with pytest.raises(ValueError):
            twos_complement(1, 0)
