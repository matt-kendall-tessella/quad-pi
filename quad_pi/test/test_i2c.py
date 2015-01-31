import unittest
import mock
from hamcrest import assert_that, is_

from quad_pi.i2c import TwosComplement, ADXL345, L3G4200D


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

    def test_GIVEN_negative_geq_minus_128_WHEN_make_from_decimal_THEN_binary_correct(self):
        decs = [-77, -128]
        bins = [0b10110011, 0b10000000]
        for idx, dec in enumerate(decs):
            twos = TwosComplement.from_decimal(dec)
            assert_that(twos.as_bin(), is_(bins[idx]))
            assert_that(twos.as_dec(), is_(dec))

    def test_GIVEN_negative_geq_minus_32768_WHEN_make_from_decimal_THEN_binary_correct(self):
        decs = [-3500, -32768]
        bins = [0b1111001001010100, 0b1000000000000000]
        for idx, dec in enumerate(decs):
            twos = TwosComplement.from_decimal(dec)
            assert_that(twos.as_bin(), is_(bins[idx]))
            assert_that(twos.as_dec(), is_(dec))

    def test_GIVEN_positive_lt_minus_32768_WHEN_make_from_decimal_THEN_raises_ValueError(self):
        with self.assertRaises(ValueError):
            twos = TwosComplement.from_decimal(-32769)

    def test_GIVEN_floats_WHEN_make_from_decimal_THEN_correctly_rounded_binary_representation(self):
        floats = [-3.3, 5.5, -0.5, 1.1]
        bins = [0b11111101, 0b00000110, 0b11111111, 0b00000001]
        for idx, num in enumerate(floats):
            twos = TwosComplement.from_decimal(num)
            assert_that(twos.as_bin(), is_(bins[idx]))

    def test_GIVEN_instance_WHEN___int__THEN_binary_representation_returned(self):
        twos = TwosComplement.from_decimal(-3)
        assert_that(int(twos), is_(0b11111101))


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

    def test_WHEN_get_range_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_bus.read_byte_data = mock.Mock(return_value=0)
        accel = ADXL345(mock_bus)
        accel.get_data_range()
        assert_that(accel._i2c._bus.read_byte_data.call_args_list[0][0], is_((0x53, 0x31)))

    def test_WHEN_get_range_THEN_output_returned_as_expected(self):
        mock_bus = mock.Mock()
        mock_bus.read_byte_data = mock.Mock(return_value=0b00000010)
        accel = ADXL345(mock_bus)
        range = accel.get_data_range()
        assert_that(range, is_(8))

    def test_GIVEN_invalid_range_WHEN_set_range_THEN_raises_ValueError(self):
        mock_bus = mock.Mock()
        accel = ADXL345(mock_bus)
        for r in [0, -2, 32, 15.99]:
            with self.assertRaises(ValueError):
                accel.set_data_range(r)

    def test_GIVEN_valid_range_WHEN_set_range_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_bus.write_byte_data = mock.Mock()
        accel = ADXL345(mock_bus)
        accel.set_data_range(16)
        assert_that(accel._i2c._bus.write_byte_data.call_args_list[0][0], is_((0x53, 0x31, 0b00000011)))

    def test_WHEN_get_rate_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_bus.read_byte_data = mock.Mock(return_value=0)
        accel = ADXL345(mock_bus)
        accel.get_data_rate()
        assert_that(accel._i2c._bus.read_byte_data.call_args_list[0][0], is_((0x53, 0x2c)))

    def test_WHEN_get_rate_THEN_output_returned_as_expected(self):
        mock_bus = mock.Mock()
        mock_bus.read_byte_data = mock.Mock(return_value=0b00001010)
        accel = ADXL345(mock_bus)
        range = accel.get_data_rate()
        assert_that(range, is_(100))

    def test_GIVEN_invalid_rate_WHEN_set_rate_THEN_raises_ValueError(self):
        mock_bus = mock.Mock()
        accel = ADXL345(mock_bus)
        for r in [0, -200, 101, 0.05]:
            with self.assertRaises(ValueError):
                accel.set_data_rate(r)

    def test_GIVEN_valid_rate_WHEN_set_rate_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_bus.write_byte_data = mock.Mock()
        accel = ADXL345(mock_bus)
        accel.set_data_rate(400)
        assert_that(accel._i2c._bus.write_byte_data.call_args_list[0][0], is_((0x53, 0x2c, 0b00001100)))

    def test_GIVEN_range_2g_WHEN_set_offset_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_bus.write_byte_data = mock.Mock()
        mock_bus.read_byte_data = mock.Mock(return_value=0b00)
        accel = ADXL345(mock_bus)
        off_x, off_y, off_z = 10, -13, 9
        accel.set_offset(off_x, off_y, off_z)
        assert_that(accel._i2c._bus.write_byte_data.call_args_list[0][0], is_((0x53, 0x1e, 0xfd)))
        assert_that(accel._i2c._bus.write_byte_data.call_args_list[1][0], is_((0x53, 0x1f, 0x03)))
        assert_that(accel._i2c._bus.write_byte_data.call_args_list[2][0], is_((0x53, 0x20, 0xfe)))


class TestL4G4200D(unittest.TestCase):

    def test_WHEN_get_range_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_bus.read_byte_data = mock.Mock(return_value=0)
        gyro = L3G4200D(mock_bus)
        gyro.get_data_range()
        assert_that(gyro._i2c._bus.read_byte_data.call_args_list[0][0], is_((0x69, 0x23)))

    def test_WHEN_get_range_THEN_output_returned_as_expetected(self):
        mock_bus = mock.Mock()
        mock_bus.read_byte_data = mock.Mock(return_value=0b10010001)
        gyro = L3G4200D(mock_bus)
        range = gyro.get_data_range()
        assert_that(range, is_(500))

    def test_GIVEN_invalid_range_WHEN_set_range_THEN_raises_ValueError(self):
        mock_bus = mock.Mock()
        gyro = L3G4200D(mock_bus)
        with self.assertRaises(ValueError):
            gyro.set_data_range(450)

    def test_GIVEN_valid_range_WHEN_set_range_THEN_i2c_called_correctly(self):
        mock_bus = mock.Mock()
        mock_bus.write_byte_data = mock.Mock()
        gyro = L3G4200D(mock_bus)
        gyro.set_data_range(2000)
        assert_that(gyro._i2c._bus.write_byte_data.call_args_list[0][0], is_(((0x69, 0x23, 0b00100000))))

    def test_WHEN_read_raw_THEN_i2c_called_correcrtly(self):
        mock_bus = mock.Mock()
        mock_vals = [0, 1, 2, 3, 4, 5]
        mock_bus.read_byte_data = mock.Mock(side_effect=mock_vals)
        gyro = L3G4200D(mock_bus)
        gyro.read(True)
        assert_that(gyro._i2c._bus.read_byte_data.call_count, is_(6))
        for idx, register in enumerate(range(0x28, 0x2e)):
            assert_that(gyro._i2c._bus.read_byte_data.call_args_list[idx][0], is_((0x69, register)))

    def test_WHEN_read_dps_THEN_output_in_dps(self):
        mock_bus = mock.Mock()
        # 3 x MSB, LSB
        mock_vals = [0, 1, 2, 3, 4, 5, 0]
        mock_bus.read_byte_data = mock.Mock(side_effect=mock_vals)
        gyro = L3G4200D(mock_bus)
        x, y, z = gyro.read()
        assert_that((x, y, z), is_((256 * (8.75 / 1000), 770* (8.75 / 1000), 1284* (8.75 / 1000))))

    def test_WHEN_read_raw_THEN_output_in_raw(self):
        mock_bus = mock.Mock()
        # 3 x MSB, LSB
        mock_vals = [0, 1, 2, 3, 4, 5]
        mock_bus.read_byte_data = mock.Mock(side_effect=mock_vals)
        gyro = L3G4200D(mock_bus)
        x, y, z = gyro.read(True)
        assert_that((x, y, z), is_((256, 770, 1284)))