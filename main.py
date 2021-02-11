#!/usr/bin/env python3

import sys
import argparse
from PyQt5 import QtWidgets
from qtgassol.ui import MainUI
from qtgassol.device import FlukeThermometer, GeManometer, HuberThermostat, DummyT, DummyP, DummyFile

parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument('-t', '--temp', type=str, default='auto',
                    help='Device for thermometer. '
                         'auto means detect the thermometer automatically. '
                         'dummy means use randomly generated temperature data. '
                         'Otherwise specify the device e.g. /dev/ttyUSB0, or a file name')
parser.add_argument('-p', '--press', type=str, default='auto',
                    help='Device for manometer. '
                         'auto means detect the manometer automatically. '
                         'dummy means use randomly generated pressure data. '
                         'Otherwise specify the device e.g. /dev/ttyUSB1, or a file name')
parser.add_argument('--thermostat', type=str, default='none',
                    help='Device for thermostat. '
                         'none means disable thermostat. '
                         'auto means detect the thermostat automatically. '
                         'Otherwise specify the device e.g. /dev/ttyACM0, or a file name')
parser.add_argument('-o', '--output', type=str, default='output.txt',
                    help='Output filename. Can also be specified from GUI.')
parser.add_argument('--dt', type=float, default=5.0,
                    help='Time interval for reading data. Can also be specified from GUI.')

opt = parser.parse_args()

if __name__ == '__main__':
    if opt.temp == 'auto':
        temp = FlukeThermometer.detect()
        if temp is None:
            print('ERROR: Thermometer not detected. Try again or specify the device.')
            sys.exit(1)
        else:
            print('Thermometer detected: %s' % temp)
    elif opt.temp == 'dummy':
        temp = DummyT()
    elif opt.temp.startswith('/dev'):
        temp = FlukeThermometer(opt.temp)
    else:
        temp = DummyFile(opt.temp, -2)

    if opt.press == 'auto':
        press = GeManometer.detect()
        if press is None:
            print('ERROR: Manometer not detected. Try again or specify the device.')
            sys.exit(1)
        else:
            print('Manometer detected: %s' % press)
    elif opt.press == 'dummy':
        press = DummyP()
    elif opt.press.startswith('/dev'):
        press = GeManometer(opt.press)
    else:
        press = DummyFile(opt.press, -1)

    if opt.thermostat == 'auto':
        thermo = HuberThermostat.detect()
        if thermo is None:
            print('ERROR: Thermostat not detected. Try again or specify the device.')
            sys.exit(1)
        else:
            print('Thermostat detected: %s' % thermo)
    elif opt.thermostat.startswith('/dev'):
        thermo = HuberThermostat(opt.thermostat)
    else:
        thermo = None

    app = QtWidgets.QApplication(sys.argv)
    ui = MainUI(temp, press, thermo, opt.output, opt.dt)
    ui.show()
    sys.exit(app.exec_())
