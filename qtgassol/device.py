import serial
import serial.tools.list_ports
import numpy as np
from datetime import datetime


class Device(object):
    '''A device'''

    def __init__(self, name=None, port=None):
        self.name = name or 'Device'
        # TODO timeout of 1s may not be reasonable
        self.port = serial.Serial(port, 9600, timeout=1.0)

    def __str__(self):
        return ('%s : %s' % (self.name, self.port))

    def read(self):
        '''
        Return -1 if there is error
        '''
        raise NotImplementedError('This method should be implemented by inheritors')


class Thermometer(Device):
    '''Thermometer'''

    def __init__(self, port):
        super().__init__('Thermometer', port)

    def read(self):
        '''
        TODO
        use in_waiting to check the available data in buffer
        read it until data are completely transmitted
        '''
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

    @staticmethod
    def detect():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            try:
                dev = Thermometer(d)
            except:
                continue

            if dev.read() != -1:
                return dev

        return None


class Manometer(Device):
    '''Pressure transducer'''

    def __init__(self, port):
        super().__init__('Manometer', port)

        # speed 2: 16000 cycles 1.0 s
        # speed 3:  8000 cycles 0.5 s
        # self.port.write(b'xQ,2\r')
        # self.port.write(b'xU,0\r')  # unit: mbar
        # self.port.write(b'x*A,1.0\r')  # send value every 1.0 s, with units
        self.port.write(b'*Q,2\r')
        self.port.write(b'*U,0\r')  # unit: mbar
        self.port.write(b'-*A,1.0\r')  # send value every 1.0 s, with units

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

    @staticmethod
    def detect():
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/ttyUSB'):
                continue

            try:
                dev = Manometer(d)
            except:
                continue

            if dev.read() != -1:
                return dev

        return None


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
        super().__init__('Dummy File')
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
