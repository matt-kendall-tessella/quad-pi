import unittest
from hamcrest import assert_that, is_

from quad_pi.i2c import TwosComplement


class TestTwosComplement(unittest.TestCase):

    def test_GIVEN_only_lsb_WHEN_get_bin_THEN_binary_correct(self):
        lsb = 0b01010101
        twos = TwosComplement(lsb)
        assert_that(twos.as_bin(), is_(lsb))

    def test_GIVEN_lsb_and_msb_overall_positive_WHEN_get_bin_THEN_binary_correct(self):
        lsb = 0b01010101
        msb = 0b00001000
        expected_bin = 0b000100001010101
        twos = TwosComplement(lsb, msb)
        assert_that(twos.as_bin(), is_(expected_bin))

    def test_GIVEN_lsb_and_msb_overall_negative_WHEN_get_bin_THEN_binary_correct(self):
        lsb = 0b11111001
        msb = 0b11111111
        expected_bin = 0b1111111111111001
        twos = TwosComplement(lsb, msb)
        assert_that(twos.as_bin(), is_(expected_bin))

    def test_GIVEN_only_lsb_negative_WHEN_get_decimal_THEN_decimal_correct(self):
        lsbs = [0b10101010, 0b11011011, 0b11110010]
        decs = [-86, -37, -14]
        for idx, lsb in enumerate(lsbs):
            twos = TwosComplement(lsb)
            assert_that(twos.as_dec(), is_(decs[idx]))

    def test_GIVEN_only_lsb_positive_WHEN_get_decimal_THEN_decimal_correct(self):
        lsbs = [0b01101001, 0b01010111]
        decs = [105, 87]
        for idx, lsb in enumerate(lsbs):
            twos = TwosComplement(lsb)
            assert_that(twos.as_dec(), is_(decs[idx]))

    def test_GIVEN_lsb_and_msb_overall_negative_WHEN_get_decimal_THEN_decimal_correct(self):
        lsb = 0b01010101
        msb = 0b10010010
        twos = TwosComplement(lsb, msb)
        assert_that(twos.as_dec(), is_(-28075))

    def test_GIVEN_lsb_and_msb_overall_positive_WHEN_get_decimal_THEN_decimal_correct(self):
        lsb = 0b01010101
        msb = 0b01010010
        twos = TwosComplement(lsb, msb)
        assert_that(twos.as_dec(), is_(21077))