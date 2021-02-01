import serial
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
        return (self.name + ': ' + str(self.port))

    def read(self):
        '''
        Return -1 if there is error
        '''
        return -1


class Thermometer(Device):
    '''Thermometer'''

    def __init__(self, port):
        super().__init__('Thermometer', port)

        self.port.write(b'T\r')

    def read(self):
        self.port.write(b'T\r')
        self.port.reset_input_buffer()
        buf = self.port.read(16)
        print(buf)

        datastr = buf.decode()
        if len(datastr):
            try:
                val = float(datastr.split(':')[1].strip().split()[0])
                return val
            except:
                pass

        return -1


class Manometer(Device):
    '''Pressure transducer'''

    def __init__(self, port):
        super().__init__('Manometer', port)
        self.port = serial.Serial(port, 9600, timeout=1.0)

        self.port.write(b'xQ,2\r')  # speed 2: 16000 cycles 1.0 s
        #       3:  8000 cycles 0.5 s
        self.port.write(b'xU,0\r')  # units: mbar
        self.port.write(b'x*A,1.0\r')  # send value every 1.0 s

    def read(self):
        self.port.write(b'-*G\r')
        self.port.reset_input_buffer()
        buf = self.port.read(13)
        print(buf)

        datastr = buf.decode()
        if len(datastr):
            try:
                val = float(datastr.split()[0])
                return val
            except:
                pass

        return -1


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
