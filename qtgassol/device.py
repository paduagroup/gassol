import serial
import numpy as np
from datetime import datetime


class device(object):
    '''A device'''

    def __init__(self, name=None, port=None):
        self.name = name or 'Device'
        if port is None:
            self.port = None
        else:
            self.port = serial.Serial(port, 9600, timeout=1.0)
        self.err = False

    def __str__(self):
        return (self.name + ': ' + str(self.port))

    def read(self):
        val = 0.0
        return val


class therm(device):
    '''Thermometer'''

    def __init__(self, port):
        super().__init__('Thermometer', port)

        self.port.write(b'T\r')

    def read(self):
        self.err = False

        self.port.write(b'T\r')
        self.port.reset_input_buffer()
        buf = self.port.read(15)

        datastr = str(buf).strip('b\'')
        if len(datastr):
            datastr = datastr.split()[1]
            try:
                float(datastr)
                val = float(datastr)
            except ValueError:
                self.err = True
        else:
            self.err = True
        return val


class press(device):
    '''Pressure transducer'''

    def __init__(self, port):
        super().__init__('Manometer', port)
        self.port = serial.Serial(port, 9600, timeout=1.0)

        self.port.write(b'xQ,2\r')  # speed 2: 16000 cycles 1.0 s
        #       3:  8000 cycles 0.5 s
        self.port.write(b'xU,0\r')  # units: mbar
        self.port.write(b'x*A,1.0\r')  # send value every 1.0 s

    def read(self):
        self.err = False

        self.port.write(b'-*G\r')
        self.port.reset_input_buffer()
        buf = self.port.read(12)

        datastr = str(buf).strip('b\'')
        if len(datastr):
            datastr = datastr.split()[0]
            try:
                val = float(datastr)
            except ValueError:
                self.err = True
        else:
            self.err = True
        return val


class dummyT(device):

    def __init__(self):
        super().__init__('dummy T')

    def read(self):
        return 25.0 + np.random.random_sample() - 0.5


class dummyP(device):

    def __init__(self):
        super().__init__('dummy P')
        self.t0 = datetime.now().timestamp()

    def read(self):
        delt = datetime.now().timestamp() - self.t0
        tau = 60.0
        return (1013.0 * 2.718 ** (- delt / tau) + 50.0 * np.random.random_sample() - 25.0)
