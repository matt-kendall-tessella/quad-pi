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

    def __int__(self):
        """
        Return the binary representation, so that this can be used with int casting
        """
        return self.as_bin()

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
    def _split_lsb_msb(cls, binary):
        """
        Split a 16 bit binary number into LSB and MSB (each 8 bits).
        :param binary: 16 bit binary number to split
        """
        msb = binary >> 8
        lsb = binary - (msb << 8)
        return lsb, msb

    @classmethod
    def _negative_to_binary(cls, decimal, bits):
        return ~ abs(decimal) + (2 ** bits + 1)

    @classmethod
    def from_decimal(cls, decimal):
        """
        Create a new TwosComplement instance from a decimal number
        :param decimal: Decimal to convert into twos complement. Must be in the range -32768 <= x < 32768.
        May be integer or floating point.
        :return: A TwosComplement instance
        :raise ValueError: if the decimal is outside of the specified range.
        """
        # Round and cast to int first:
        decimal = int(round(decimal))
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
        self._bus.write_byte_data(self._address, register_address, int(byte_data))


class ADXL345(object):
    """
    Interface to an ADXL345 3-axis Accelerometer
    """

    # Device address
    ADDRESS = 0x53

    # Device Registers
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
    DATA_RANGES = bidict({
        2: 0b00,
        4: 0b01,
        8: 0b10,
        16: 0b11
    })

    # Data range (+/-g) --> Scale factor (mg / LSB)
    SCALE_FACTORS = {
        2: 3.9,
        4: 7.8,
        8: 15.6,
        16: 31.2
    }

    # Scale factor of values in the offset registers (mg / LSB)
    OFFSET_REGISTERS_SCALE_FACTOR = 15.6

    # Data rate (Hz) --> Rate bits value
    DATA_RATES = bidict({
        3200: 0b1111,
        1600: 0b1110,
        800: 0b1101,
        400: 0b1100,
        200: 0b1011,
        100: 0b1010,
        50: 0b1001,
        25: 0b1000,
        12.5: 0b0111,
        6.25: 0b0110,
        3.13: 0b0101,
        1.56: 0b0100,
        0.78: 0b0011,
        0.39: 0b0010,
        0.20: 0b0001,
        0.10: 0b0000
    })

    _i2c = None

    def __init__(self, i2c_bus):
        """
        Create a new ADXL345 device
        :param i2c_bus: Configured smbus.SMBus instance to use for connections
        """
        self._i2c = I2CDevice(i2c_bus, self.ADDRESS)

    def read(self):
        """
        Read the decimal values (raw LSB) for the three axes from the accelerometer. Values are not converted into
        units of g but if the board has had an offset saved in this power cycle then this is subtracted onboard.
        :returns An (x,y,z) tuple of the raw LSB
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

    def get_data_rate(self):
        """
        Find the accelerometers current data rate.
        """
        bin_rate = self._i2c[self.BW_RATE]
        return self.DATA_RATES[:bin_rate % 16]  # Takes the 4 right hand bits

    def set_data_rate(self, rate):
        """
        Set the accelerometer's output data rate.
        :param rate: The output data rate to set (Hz). Must be one of the ADXL345's supported data rates (see datasheet).
        This includes 50Hz, 100Hz, 200Hz, 400Hz, 800Hz
        """
        if rate in self.DATA_RATES:
            setting = self.DATA_RATES[rate]
            self._i2c[self.BW_RATE] = setting
        else:
            raise ValueError("%s is not an acceptable output data rate - check the datasheet for valid values." % rate)

    def get_data_range(self):
        """
        Find out the accelerometer's current data range.
        """
        bin_range = self._i2c[self.DATA_FORMAT]
        return self.DATA_RANGES[:bin_range % 4]  # Takes the 2 right hand bits

    def set_data_range(self, data_range):
        """
        Set the data range (from +/- 2,4,8,16 g).
        :param data_range: Integer range (choose from +/- 2,4,8,16 g).
        """
        if data_range in self.DATA_RANGES:
            setting = self.DATA_RANGES[data_range]
            self._i2c[self.DATA_FORMAT] = setting
        else:
            raise ValueError("%s is not an acceptable range - choose from 2,4,8,16." % data_range)

    def set_offset(self, offset_x, offset_y, offset_z):
        """
        Set the onboard zero-g offset.

        This takes the reading in LSB that
        :param offset_x: x-axis 0g reading (LSB)
        :param offset_y: y-axis 0g reading (LSB)
        :param offset_z: z-axis 1g reading (LSB)
        """
        # First rescale the data to match the offset registers
        data_range = self.get_data_range()
        scaled_x = self._scale_to_match_offset_register(offset_x, data_range)
        scaled_y = self._scale_to_match_offset_register(offset_y, data_range)
        scaled_z = self._scale_to_match_offset_register(offset_z, data_range)

        # Values get stored in registers as negatives
        self._i2c[self.OFSX] = TwosComplement.from_decimal(- scaled_x)
        self._i2c[self.OFSY] = TwosComplement.from_decimal(- scaled_y)
        self._i2c[self.OFSZ] = TwosComplement.from_decimal(- scaled_z)

    def _scale_to_match_offset_register(self, value, data_range):
        """
        Scale a value to match the scale of the offset register
        :param value: Value to scale
        :param data_range: Currently selected board data range (+/- g)
        """
        scale_factor = self.SCALE_FACTORS[data_range]
        return value * (scale_factor / self.OFFSET_REGISTERS_SCALE_FACTOR)


class L3G4200D(object):
    """
    Interface to an L3g4200D Gyroscope
    """

    ADDRESS = 0x69

    CTRL_REG1 = 0x20
    CTRL_REG2 = 0x21
    CTRL_REG3 = 0x22
    CTRL_REG4 = 0x23
    CTRL_REG5 = 0x24
    OUT_X_L = 0x28
    OUT_X_H = 0x29
    OUT_Y_L = 0x2a
    OUT_Y_H = 0x2b
    OUT_Z_L = 0x2c
    OUT_Z_H = 0x2d

    # Data range (+/-dps) --> Range bits value
    DATA_RANGES = bidict({
        250: 0b00,
        500: 0b01,
        2000: 0b10
    })

    # Data range (+/-dps) --> Scale factor (mdps / LSB)
    SCALE_FACTORS = {
        250: 8.75,
        500: 17.50,
        2000: 70,
    }

    _i2c = None

    def __init__(self, i2c_bus):
        """
        Create a new L3G4200D device
        :param i2c_bus: Configured smbus.SMBus instance to use for connections
        """
        self._i2c = I2CDevice(i2c_bus, self.ADDRESS)

    def read(self, raw=False):
        """
        Read the gyroscope rates out for each axis
        :param raw: If True, return rates in raw format (LSB), if False (default)
        :returns An (x,y,z) tuple of either raw LSB or degrees per second
        """
        x = TwosComplement(self._i2c[self.OUT_X_L], self._i2c[self.OUT_X_H])
        y = TwosComplement(self._i2c[self.OUT_Y_L], self._i2c[self.OUT_Y_H])
        z = TwosComplement(self._i2c[self.OUT_Z_L], self._i2c[self.OUT_Z_H])
        if raw:
            return x.as_dec(), y.as_dec(), z.as_dec()
        else:
            data_range = self.get_data_range()
            dps_per_lsb = self.SCALE_FACTORS[data_range] / 1000.0
            return dps_per_lsb * x.as_dec(), dps_per_lsb * y.as_dec(), dps_per_lsb * z.as_dec()

    def set_data_range(self, data_range):
        """
        Set the gyroscope's data range.
        :param data_range: Data range to set in degrees per second
        """
        if data_range in self.DATA_RANGES:
            full_scale_bits = self.DATA_RANGES[data_range]
            self._i2c[self.CTRL_REG4] = full_scale_bits << 4
        else:
            raise ValueError("%s is not an acceptable range - choose from 250,500,2000." % data_range)

    def get_data_range(self):
        """
        Get the gyroscopes currently set data range in degrees per second
        """
        bin_range = self._i2c[self.CTRL_REG4]
        # The full scale bits are 5 and 6 (zero-index from right).
        full_scale_bits = (bin_range >> 4) % 4
        return self.DATA_RANGES[:full_scale_bits]

