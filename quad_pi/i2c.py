from smbus import SMBus


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
        self.bus = i2c_bus
        self.bus = SMBus()
        self.address = device_address

    def __getitem__(self, register_address):
        return self.bus.read_byte_data(self.address, register_address)

    def __setitem__(self, register_address, byte_data):
        self.bus.write_byte_data(self.address, register_address, byte_data)


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

    def __init__(self, i2c_bus):
        self.i2c = I2CDevice(i2c_bus, self.ADDRESS)

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
        self.i2c[self.POWER_CTL] = data

    def stop(self):
        """
        Signal the ADXl345 to stop measurements by placing it in 'standby' mode.
        This is achieved by clearing the 'measure' bit of POWER_CTL
        """
        data = 0b00000000
        self.i2c[self.POWER_CTL] = data

    def set_rate(self, rate):
        # TODO
        # Use BW_RATE, see power mode as well
        pass

    def set_data_format(self):
        # TODO
        # DATA FORMAT
        pass

    def self_test(self):
        # TODO
        # DATA FORMAT
        pass

    def read_data(self):
        # TODO
        # split into 3 axis? at least for private methods
        pass
