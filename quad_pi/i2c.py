from smbus import SMBus
from bidict import bidict


class TwosComplement(object):

    _bin_val = None
    _bits = 16

    def __init__(self, lsb, msb=None):
        """
        Create a new two's complement number
        :param lsb: The least significant byte of the number.
        :param msb: An optional second most significant byte.
        """
        if msb is None:
            self._bin_val = lsb
            self._bits = 8
        else:
            self._bin_val = (msb << 8) + lsb
            self._bits = 16

    def as_dec(self):
        """
        Return the value of this number as a decimal
        """
        sign_bit = self._bin_val >> self._bits - 1
        if sign_bit:
            # Flip the bits after the sign
            data_bits = self._bin_val - 2**self._bits
            return -(~ data_bits + 1)
        else:
            return self._bin_val

    def as_bin(self):
        """
        Return the binary (two's complement) value of this number
        """
        return self._bin_val

    @classmethod
    def _split_lsb_msb(cls, bin):
        msb = bin >> 8
        lsb = bin - (msb << 8)
        return lsb, msb

    @classmethod
    def _negative_to_binary(cls, decimal, bits):
        return ~ abs(decimal) + (2 ** bits + 1)

    @classmethod
    def from_decimal(cls, decimal):
        """
        Create a new TwosComplement instance from a decimal number
        :param decimal: Decimal to convert into twos complement. Must be in the range -32768 <= x < 32768
        :return: A TwosComplement instance
        :raise ValueError: if the decimal is outside of the specified range.
        """
        if decimal >= 0:
            # Positive - we can use the binary as is
            if decimal < 128:
                # 8 bits - just use LSB
                return cls(decimal)
            elif decimal < 32768:
                # 16 bits - split into LSB and MSB
                lsb, msb = cls._split_lsb_msb(decimal)
                return cls(lsb, msb)
            else:
                raise ValueError("Decimal must be an 8 or 16 bit integer")
        else:
            # Negative, take off 1, flip bits, add negative bit
            if decimal >= -128:
                # 8 bits - just use LSB
                bits = 8
                binary = cls._negative_to_binary(decimal, bits)
                return cls(binary)
            elif decimal >= - 32768:
                bits = 16
                binary = cls._negative_to_binary(decimal, bits)
                lsb, msb = cls._split_lsb_msb(binary)
                return cls(lsb, msb)
            else:
                raise ValueError("Decimal must be an 8 or 16 bit integer")


class I2CDevice(object):
    """
    Represents any I2C device with a specific address.
    """

    def __init__(self, i2c_bus, device_address):
        """
        Initialise a new I2C device.
        :param i2c_bus: Configured smbus.SMBus instance
        :param device_address: I2C Address of device
        """
        self._bus = i2c_bus
        self._address = device_address

    def __getitem__(self, register_address):
        """
        Retrieve a value from a given register on this device
        """
        return self._bus.read_byte_data(self._address, register_address)

    def __setitem__(self, register_address, byte_data):
        """
        Write a value to a given register on this device
        """
        self._bus.write_byte_data(self._address, register_address, byte_data)


class ADXL345(object):
    """
    Interface to an ADXL345 3-axis Accelerometer
    """

    ADDRESS = 0x53

    DEVID = 0x0
    THRESH_TAP = 0x1d
    OFSX = 0x1e
    OFSY = 0x1f
    OFSZ = 0x20
    DUR = 0x21
    LATENT = 0x22
    WINDOW = 0x23
    THRESH_ACT = 0x24
    THRESH_INACT = 0x25
    TIME_INACT = 0x26
    ACT_INACT_CTL = 0x27
    THRESH_FF = 0x28
    TIME_FF = 0x29
    TAP_AXES = 0x2a
    ACT_TAP_STATUS = 0x2b
    BW_RATE = 0x2c
    POWER_CTL = 0x2d
    INT_ENABLE = 0x2e
    INT_MAP = 0x2f
    INT_SOURCE = 0x30
    DATA_FORMAT = 0x31
    DATAX0 = 0x32
    DATAX1 = 0x33
    DATAY0 = 0x34
    DATAY1 = 0x35
    DATAZ0 = 0x36
    DATAZ1 = 0x37
    FIFO_CTL = 0x39
    FIFO_STATUS = 0x39

    # Data range (+/-g) --> Range bits value
    DATA_RANGES = bidict({2: 0b00,
                          4: 0b01,
                          8: 0b10,
                          16: 0b11})

    _i2c = None

    def __init__(self, i2c_bus):
        """
        Create a new ADXL345 device
        :param i2c_bus: Configured smbus.SMBus instance to use for connections
        """
        self._i2c = I2CDevice(i2c_bus, self.ADDRESS)

    def read(self):
        """
        Read the decimal values (raw ADU) for the three axes from the accelerometer. Values are not converted into
        units of g but if the board has had an offset saved in this power cycle then this is subtracted onboard.
        :returns An (x,y,z) tuple of the raw ADU
        """
        x, y, z = self._get_raw_xyz()
        return x.as_dec(), y.as_dec(), z.as_dec()

    def _get_raw_xyz(self):
        """
        Get the binary (twos complement) reading for each axis
        """
        x = TwosComplement(self._i2c[self.DATAX0], self._i2c[self.DATAX1])
        y = TwosComplement(self._i2c[self.DATAY0], self._i2c[self.DATAY1])
        z = TwosComplement(self._i2c[self.DATAZ0], self._i2c[self.DATAZ1])
        return x, y, z

    def set_offset(self):
        # TODO
        # Use OFSX, OFSY, OFSZ (0x1e, 0x1f, 0x20)
        pass

    def start(self):
        """
        Signal the ADXL345 to begin measurements by moving it from 'standby' mode into 'measure' mode.
        This is achieved by setting the 'measure' bit of POWER_CTL
        """
        data = 0b00001000
        self._i2c[self.POWER_CTL] = data

    def stop(self):
        """
        Signal the ADXl345 to stop measurements by placing it in 'standby' mode.
        This is achieved by clearing the 'measure' bit of POWER_CTL
        """
        data = 0b00000000
        self._i2c[self.POWER_CTL] = data

    def set_rate(self, rate):
        # TODO
        # Use BW_RATE, see power mode as well
        pass

    def get_data_range(self):
        """
        Find out the accelerometer's set data range.
        """
        bin_range = self._i2c[self.DATA_FORMAT]
        return self.DATA_RANGES[:bin_range % 4]

    def set_data_range(self, range):
        """
        Set the data range (from +/- 2,4,8,16 g).
        :param range: Integer range (choose from +/- 2,4,8,16 g).
        """
        if range in self.DATA_RANGES:
            setting = self.DATA_RANGES[range]
            self._i2c[self.DATA_FORMAT] = setting
        else:
            raise ValueError("%s is not an acceptable range - choose from 2,4,8,16")

    def self_test(self):
        # TODO
        # DATA FORMAT
        pass

