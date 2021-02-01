import serial
import serial.tools.list_ports
import numpy as np
from datetime import datetime


class Device(object):
    '''A device'''

    def __init__(self, name=None, port=None):
        self.name = name or 'Device'
        if port is None:
            self.port = None
        else:
            self.port = serial.Serial(port, 9600, timeout=1.0)

    def __str__(self):
        return ('%s : %s' % (self.name, self.port))

    def read(self):
        '''
        Return -1 if there is error
        '''
        return -1


class Thermometer(Device):
    '''Thermometer'''

    def __init__(self, port):
        super().__init__('Thermometer', port)

    def read(self):
        self.port.write(b'T\r')
        self.port.reset_input_buffer()
        buf = self.port.read(16)
        print(buf)

        # make sure the format is correct
        # b'T\r\nt:   32.728 C'
        words = buf.decode().split()
        if len(words) < 2 or words[-1] != 'C':
            return -1

        try:
            val = float(words[-2])
        except:
            return -1
        else:
            return val


class Manometer(Device):
    '''Pressure transducer'''

    def __init__(self, port):
        super().__init__('Manometer', port)

        # speed 2: 16000 cycles 1.0 s
        # speed 3:  8000 cycles 0.5 s
        self.port.write(b'xQ,2\r')
        self.port.write(b'xU,0\r')  # unit: mbar
        self.port.write(b'x*A,1.0\r')  # send value every 1.0 s

    def read(self):
        self.port.write(b'-*G\r')
        self.port.reset_input_buffer()
        buf = self.port.read(13)
        print(buf)

        # make sure the format is correct
        # b'962.43 mbar\r\n'
        words = buf.decode().split()
        if len(words) < 2 or words[-1] != 'mbar':
            return -1

        try:
            val = float(words[-2])
        except:
            return -1
        else:
            return val


class DummyT(Device):
    def __init__(self):
        super().__init__('Dummy T')

    def read(self):
        return 25.0 + np.random.random_sample() - 0.5


class DummyP(Device):
    def __init__(self):
        super().__init__('Dummy P')
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
        super().__init__('File')
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


class DeviceDetector():
    '''
    Detect USB device for thermometer and manometer.
    '''

    @staticmethod
    def detect_thermometer():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            dev = serial.Serial(d, 9600, timeout=1.0)
            dev.write(b'T\r')
            buf = dev.read(16)
            if buf.decode().strip().endswith('C'):
                return Thermometer(d)

        return None

    @staticmethod
    def detect_manometer():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            dev = serial.Serial(d, 9600, timeout=1.0)
            dev.write(b'x*R\r')
            buf = dev.read(13)
            if buf.decode().strip().endswith('mbar'):
                return Manometer(d)

        return None
