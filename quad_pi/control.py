from datetime import datetime
import math

from quad_pi.i2c import ADXL345, L3G4200D


class AHRS(object):
    """
    Attitude Heading Reference System
    """

    _last_read_time = None
    _int_roll = 0.0
    _int_pitch = 0.0

    def __init__(self, accel, gyro, k=0.97):
        """
        Create an new Attitude Heading Reference System
        :param accel: Accelerometer (already started)
        :param gyro: Gyroscope (already started)
        :param k: Complementary filter constant K.
        Higher K -> more gyroscope input; lower K -> more accelerometer input.
        """
        self._accel = accel
        self._gyro = gyro
        self._k = k

    @classmethod
    def create_from_bus(cls, i2c_bus, k=0.97):
        """
        Create an AHRS instance from a given SMBUS.
        Uses ADXL345 accelerometer and L3G4200D gyroscope as default devices
        :param i2c_bus: Configured smbus.SMBus instance to use for connections
        :param k: Complementary filter constant K.
        Higher K -> more gyroscope input; lower K -> more accelerometer input.
        """
        accel = ADXL345(i2c_bus)
        gyro = L3G4200D(i2c_bus)
        accel.start()
        gyro.start()
        return cls(accel, gyro, k)

    def calculate(self):
        """
        Read and calculate the attitude and heading information
        :returns A tuple of (pitch, roll, heading)
        """
        a_pitch, a_roll = self._get_accel_attitude()
        g_dx, g_dy, g_dz = self._get_gyro_angles()
        if None in (g_dx, g_dy, g_dz):
            self._int_pitch = a_pitch
            self._int_roll = a_roll
        else:
            self._int_pitch = self._k * (self._int_pitch + g_dx) + (1 - self._k) * a_roll
            self._int_roll = self._k * (self._int_roll + g_dy) + (1 - self._k) * a_roll
        return self._int_pitch, self._int_roll, 360

    def _get_accel_attitude(self):
        """
        Get the accelerometer's estimate for pitch and roll
        :return: Tuple of (pitch, roll)
        """
        x, y, z = self._accel.read()
        pitch = math.atan2(-y, x)
        roll = math.atan2(x, math.sqrt(y**2 + x**2))
        return math.degrees(pitch), math.degrees(roll)

    def _get_gyro_angles(self):
        """
        Get the gyroscope angular deltas since the last read
        :return:
        """
        dx, dy, dz = self._gyro.read()
        if self._last_read_time is None:
            return None, None, None
        time_now = datetime.now()
        dt = (time_now - self._last_read_time).total_seconds()
        self._last_read_time = time_now
        return dx * dt, dy * dt, dz * dt

