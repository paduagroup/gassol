import time
import serial
import serial.tools.list_ports
import numpy as np
from datetime import datetime


class Device(object):
    '''A device'''

    def __init__(self, port=None):
        self.port = port
        if port is not None:
            self.serial = serial.Serial(port, 9600, timeout=0)

    def __str__(self):
        return ('<%s: %s>' % (self.__class__.__name__, self.port))

    def read(self, **kwargs):
        '''
        Return -1 if there is error
        '''
        raise NotImplementedError('Method not supported')

    def set(self, val, **kwargs):
        '''
        Return -1 if there is error
        '''
        raise NotImplementedError('Method not supported')


class FlukeThermometer(Device):
    '''Thermometer'''

    def __init__(self, port):
        super().__init__(port)

        # set unit to C
        self.serial.write(b'U=C\r')
        # disable timestamp
        self.serial.write(b'ST=OFF\r')
        # disable data auto transmission
        self.serial.write(b'SA=0\r')

        # clean buffer. It can take a while for data been fully transmitted
        time.sleep(1.0)
        self.serial.reset_input_buffer()

    def read(self, timeout=1.0, debug=False):
        self.serial.reset_input_buffer()
        self.serial.write(b'T\r')

        # retrieve data from serial port
        # b'T\r\nt:   32.728 C\r\n'
        current_time = time.time()
        buf = b''
        while True:
            if time.time() - current_time > timeout:
                if debug:
                    print('ERROR: timeout exceeded:', buf)
                return -1

            time.sleep(0.1)

            buf += self.serial.read(100)  # read up to 100 bytes

            if buf.endswith(b'C\r\n'):
                break

        if debug:
            print(buf)

        try:
            val = float(buf.decode().split()[-2])
        except:
            return -1

        return val

    @staticmethod
    def detect():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            try:
                dev = FlukeThermometer(d)
            except:
                continue

            if dev.read() != -1:
                return dev

        return None


class GeManometer(Device):
    '''Pressure transducer'''

    def __init__(self, port):
        super().__init__(port)

        # speed 2: 16000 cycles 1.0 s
        self.serial.write(b'*Q,2\r')
        # unit: mbar
        self.serial.write(b'*U,0\r')
        # data auto transmission cannot be disabled for manometer in direct mode
        # set its interval to 9999 seconds, so it won't interfere with read() too much
        # a leading char (- or whatever) means with unit
        self.serial.write(b'-*A,9999.0\r')

        # clean buffer. It can take a while for data been fully transmitted
        time.sleep(1.0)
        self.serial.reset_input_buffer()

    def read(self, timeout=1.0, debug=False):
        self.serial.reset_input_buffer()
        self.serial.write(b'-*G\r')

        # retrieve data from serial port
        # b'962.43 mbar\r\n'
        current_time = time.time()
        buf = b''
        while True:
            if time.time() - current_time > timeout:
                if debug:
                    print('ERROR: timeout exceeded:', buf)
                return -1

            time.sleep(0.1)

            buf += self.serial.read(100)  # read up to 100 bytes

            if buf.endswith(b'mbar\r\n'):
                break

        if debug:
            print(buf)

        try:
            val = float(buf.decode().split()[-2])
        except:
            return -1

        return val

    @staticmethod
    def detect():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            try:
                dev = GeManometer(d)
            except:
                continue

            if dev.read() != -1:
                return dev

        return None


class HuberThermostat(Device):
    '''
    Huber Thermostat
    TODO to be implemented
    '''

    def __init__(self, port):
        super().__init__(port)

        # clean buffer. It can take a while for data been fully transmitted
        time.sleep(1.0)
        self.serial.reset_input_buffer()

    def read(self):
        return -1

    def set(self, val, timeout=1.0, debug=False):
        pass

    @staticmethod
    def detect():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            try:
                dev = JulaboThermostat(d)
            except:
                continue

            if dev.read() != -1:
                return dev

        return None


class JulaboThermostat(Device):
    '''
    Julabo Thermostat
    TODO to be implemented
    '''

    def __init__(self, port):
        super().__init__(port)

        # clean buffer. It can take a while for data been fully transmitted
        time.sleep(1.0)
        self.serial.reset_input_buffer()

    def read(self):
        return -1

    def set(self, val, timeout=1.0, debug=False):
        pass

    @staticmethod
    def detect():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            try:
                dev = JulaboThermostat(d)
            except:
                continue

            if dev.read() != -1:
                return dev

        return None


class DummyT(Device):
    def __init__(self):
        super().__init__()

    def read(self):
        return 25.0 + np.random.random_sample() - 0.5


class DummyP(Device):
    def __init__(self):
        super().__init__()
        self.t0 = datetime.now().timestamp()

    def read(self):
        delt = datetime.now().timestamp() - self.t0
        tau = 60.0
        return (1013.0 * 2.718 ** (- delt / tau) + 50.0 * np.random.random_sample() - 25.0)


class DummyFile(Device):
    '''
    Read data from file. For debug only.
    '''

    def __init__(self, filename, column):
        super().__init__()
        with open(filename) as f:
            self.lines = f.read().splitlines()

        self._current_line = 0
        self.column = column

    def read(self):
        if self._current_line >= len(self.lines):
            return -1

        while True:
            line = self.lines[self._current_line]
            self._current_line += 1
            if line.startswith('#'):
                continue

            words = line.strip().split()
            return float(words[self.column])
