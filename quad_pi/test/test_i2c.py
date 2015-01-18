import unittest
import mock
from hamcrest import assert_that, is_

from quad_pi.i2c import TwosComplement, ADXL345


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

    def test_GIVEN_zero_WHEN_make_from_decimal_THEN_binary_correct(self):
        twos = TwosComplement.from_decimal(0)
        assert_that(twos.as_bin(), is_(0b0))
        assert_that(twos.as_dec(), is_(0))

    def test_GIVEN_positive_leq_127_WHEN_make_from_decimal_THEN_binary_correct(self):
        decs = [66, 127]
        bins = [0b1000010, 0b01111111]
        for idx, dec in enumerate(decs):
            twos = TwosComplement.from_decimal(dec)
            assert_that(twos.as_bin(), is_(bins[idx]))
            assert_that(twos.as_dec(), is_(dec))

    def test_GIVEN_positive_leq_32767_WHEN_make_from_decimal_THEN_binary_correct(self):
        decs = [300, 32767]
        bins = [0b100101100, 0b0111111111111111]
        for idx, dec in enumerate(decs):
            twos = TwosComplement.from_decimal(dec)
            assert_that(twos.as_bin(), is_(bins[idx]))
            assert_that(twos.as_dec(), is_(dec))

    def test_GIVEN_positive_gt_32767_WHEN_make_from_decimal_THEN_raises_ValueError(self):
        with self.assertRaises(ValueError):
            twos = TwosComplement.from_decimal(32768)

    def test_GIVEN_negative_geq_minus_128_WHEN_make_from_decimal_THEN_binary_products(self):
        decs = [-77, -128]
        bins = [0b10110011, 0b10000000]
        for idx, dec in enumerate(decs):
            twos = TwosComplement.from_decimal(dec)
            assert_that(twos.as_bin(), is_(bins[idx]))
            assert_that(twos.as_dec(), is_(dec))

    def test_GIVEN_negative_geq_minus_32768_WHEN_make_from_decimal_THEN_binary_products(self):
        decs = [-3500, -32768]
        bins = [0b1111001001010100, 0b1000000000000000]
        for idx, dec in enumerate(decs):
            twos = TwosComplement.from_decimal(dec)
            assert_that(twos.as_bin(), is_(bins[idx]))
            assert_that(twos.as_dec(), is_(dec))

    def test_GIVEN_positive_lt_minus_32768_WHEN_make_from_decimal_THEN_raises_ValueError(self):
        with self.assertRaises(ValueError):
            twos = TwosComplement.from_decimal(-32769)


class TestADXL345(unittest.TestCase):

    def test_WHEN_read_data_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_vals = [0, 1, 2, 3, 4, 5]
        mock_bus.read_byte_data = mock.Mock(side_effect=mock_vals)
        accel = ADXL345(mock_bus)
        x, y, z = accel.read()
        assert_that(accel._i2c._bus.read_byte_data.call_count, is_(6))
        for idx, register in enumerate(range(0x32, 0x38)):
            assert_that(accel._i2c._bus.read_byte_data.call_args_list[idx][0], is_((0x53, register)))

    def test_GIVEN_mock_smbus_WHEN_read_data_THEN_output_data_returned_as_expected(self):
        mock_bus = mock.Mock()
        # 3 x MSB, LSB
        mock_vals = [0, 1, 2, 3, 4, 5]
        mock_bus.read_byte_data = mock.Mock(side_effect=mock_vals)
        accel = ADXL345(mock_bus)
        x, y, z = accel.read()
        assert_that((x, y, z), is_((256, 770, 1284)))