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
    def detect(debug=False):
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/tty'):
                continue

            try:
                dev = FlukeThermometer(d)
            except:
                continue

            if dev.read(debug=debug) != -1:
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
    def detect(debug=False):
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/tty'):
                continue

            try:
                dev = GeManometer(d)
            except:
                continue

            if dev.read(debug=debug) != -1:
                return dev

        return None


class Thermostat(Device):
    '''
    A thermostat supports heating over time
    '''

    def __init__(self, port):
        super().__init__(port)

        self._timestamp_temp = []

    def preset(self, string):
        '''
        Preset the heating scheme.
        Can be isothermal or constant rate heating.
        e.g. '30' means set temperature to 30.
        '30, 10, 50' means set initial T to 30, and heat up to 50 in 10 minutes, then keep constant at 50.
        '30, 10, 50; 2, 40' means set initial T to 30, and heating up to 50 in 10 minutes,
        then cool down to 40 in 2 minutes, then keep constant at 40.
        '30, 10, 50; 2, 40; 5, 50; ....' will be similar.
        There is no limit for the number of cycles.
        '''
        timestamp = time.time()
        _timestamp_temp = []
        if ',' not in string:
            try:
                val = float(string)
            except:
                return False

            _timestamp_temp = [[timestamp, val]]

        elif ';' not in string:
            words = string.strip().split(',')
            if len(words) != 3:
                return False
            try:
                values = list(map(float, words))
            except:
                return False

            _timestamp_temp = [[timestamp, values[0]]]
            _timestamp_temp.append([timestamp + values[1] * 60, values[2]])

        else:
            spans = string.strip().split(';')
            for i, span in enumerate(spans):
                words = span.strip().split(',')
                if i == 0:
                    if len(words) != 3:
                        return False

                    try:
                        values = list(map(float, words))
                    except:
                        return False

                    _timestamp_temp = [[timestamp, values[0]]]
                    _timestamp_temp.append([timestamp + values[1] * 60, values[2]])

                else:
                    if len(words) != 2:
                        return False

                    try:
                        values = list(map(float, words))
                    except:
                        return False

                    _timestamp_temp.append([_timestamp_temp[-1][0] + values[0] * 60, values[1]])

        self._timestamp_temp = _timestamp_temp
        return True

    def get_preset(self, timestamp=None):
        if not self.has_preset:
            raise Exception('Preset not exists')

        if timestamp is None:
            timestamp = time.time()

        if len(self._timestamp_temp) == 1:
            return self._timestamp_temp[0][1]

        if timestamp <= self._timestamp_temp[0][0]:
            return self._timestamp_temp[0][1]

        if timestamp >= self._timestamp_temp[-1][0]:
            return self._timestamp_temp[-1][1]

        for i, (k, v) in enumerate(self._timestamp_temp):
            if timestamp >= k:
                k_next = self._timestamp_temp[i + 1][0]
                if timestamp <= k_next:
                    return v + (self._timestamp_temp[i + 1][1] - v) / (k_next - k) * (timestamp - k)

    @property
    def has_preset(self):
        return len(self._timestamp_temp) > 0


class HuberThermostat(Thermostat):
    '''
    Huber Thermostat
    '''

    def __init__(self, port):
        super().__init__(port)

        # clean buffer. It can take a while for data been fully transmitted
        time.sleep(1.0)
        self.serial.reset_input_buffer()

        self._preset = {}  # {t_start, t_end: duration, temp: duration,

    def read(self, timeout=1.0, debug=False):
        self.serial.reset_input_buffer()
        self.serial.write(b'{M00****\r\n')

        # retrieve data from serial port
        # the temperature is represented in hex format ****
        # b'{S00****\r\n'
        current_time = time.time()
        buf = b''
        while True:
            if time.time() - current_time > timeout:
                if debug:
                    print('ERROR: timeout exceeded:', buf)
                return -1

            time.sleep(0.1)

            buf += self.serial.read(100)  # read up to 100 bytes

            if buf.startswith(b'{S00') and buf.endswith(b'\r\n'):
                break

        if debug:
            print(buf)

        try:
            str_hex = buf.decode().strip()[-4:]
            val = int(str_hex, 16)
            # temperature ranges from -151 to 500
            if val > 50000:
                val -= 65536
            val /= 100
        except:
            return -1

        return val

    def set(self, T, timeout=1.0, debug=False):
        '''
        TODO
        Huber Thermostat support temperature range from -151 to 500.
        However, -1 is used to mean failure in this code.
        Be careful.
        '''
        if T < -151 or T > 500:
            return -1

        val = T * 100
        if val < 0:
            val += 65536
        cmd = '{M00%04X\r\n' % round(val)
        self.serial.write(cmd.encode())

        return self.read(timeout=timeout, debug=debug)

    @staticmethod
    def detect(debug=False):
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/tty'):
                continue

            try:
                dev = HuberThermostat(d)
            except:
                continue

            if dev.read(debug=debug) != -1:
                return dev

        return None


class JulaboThermostat(Thermostat):
    '''
    Julabo Thermostat
    TODO to be implemented
    '''

    def __init__(self, port):
        super().__init__(port)

        # clean buffer. It can take a while for data been fully transmitted
        time.sleep(1.0)
        self.serial.reset_input_buffer()

    def read(self, timeout=1.0, debug=False):
        return -1

    def set(self, val, timeout=1.0, debug=False):
        pass

    @staticmethod
    def detect(debug=False):
        devices = [p.device for p in serial.tools.list_ports.comports()]
        for d in devices:
            if not d.startswith('/dev/tty'):
                continue

            try:
                dev = JulaboThermostat(d)
            except:
                continue

            if dev.read(debug=debug) != -1:
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
