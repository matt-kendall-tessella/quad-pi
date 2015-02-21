import unittest
import datetime as dt
from mock import Mock, patch

from hamcrest import is_, assert_that, close_to

from quad_pi.control import AHRS


class TestAHRS(unittest.TestCase):

    class MockDatetime():

        time = dt.datetime(2012, 1, 1)

        def now(self):
            self.time += dt.timedelta(milliseconds=10)
            return self.time

    def test_GIVEN_k_is_0_WHEN_calculate_THEN_accel_attitude_correct(self):
        mock_accel = Mock()
        mock_outs = [(1, 2, 254)]
        mock_accel.read = Mock(side_effect=mock_outs)
        mock_gyro = Mock
        mock_gyro.read = Mock(return_value=(0, 0, 0))
        ahrs = AHRS(mock_accel, mock_gyro, k=0.0)
        pitch, roll, hdg = ahrs.calculate()
        assert_that(pitch, close_to(-0.22557277, 1e-5))  # Should be nearly 0 deg
        assert_that(roll, close_to(0.451135051, 1e-5))  # Should be nearly 0 deg
        assert_that(hdg, is_(360))

    @patch('quad_pi.control.datetime', MockDatetime())
    def test_GIVEN_k_is_1_WHEN_calculate_THEN_gyro_attitude_correct(self):
        mock_accel = Mock()
        mock_accel.read = Mock(return_value=(0, 0, 0))
        mock_gyro = Mock()
        mock_outs = [(1000, -2000, 3000), (1000, -2000, 3000)]
        mock_gyro.read = Mock(side_effect=mock_outs)
        ahrs = AHRS(mock_accel, mock_gyro, k=1.0)
        pitch, roll, hdg = ahrs.calculate()
        # First calculation results in accelerometer pitch:
        assert_that(pitch, close_to(0, 1e-5))  # Should be nearly 0 deg
        assert_that(roll, close_to(0, 1e-5))  # Should be nearly 0 deg
        assert_that(hdg, is_(360))
        # Second calculation uses the gyro
        pitch, roll, hdg = ahrs.calculate()
        assert_that(pitch, close_to(10, 1e-5))  # Should be nearly 0 deg
        assert_that(roll, close_to(-20, 1e-5))  # Should be nearly 0 deg
        assert_that(hdg, is_(360))
