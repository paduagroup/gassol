#!/usr/bin/env python3

import sys
import argparse
from PyQt5 import QtWidgets
from qtgassol.ui import MainUI
from qtgassol.device import Thermometer, Manometer, DummyT, DummyP, DummyFile

parser = argparse.ArgumentParser()
parser.add_argument('-t', '--temp', type=str, default='dummy', help='Device for thermometer')
parser.add_argument('-p', '--press', type=str, default='dummy', help='Device for manometer')
parser.add_argument('-o', '--output', type=str, default='output.txt', help='Output filename')
parser.add_argument('--dt', type=float, default=1.0, help='Time interval for reading data')

opt = parser.parse_args()

if __name__ == '__main__':
    if opt.temp == 'dummy':
        temp = DummyT()
    else:
        temp = Thermometer(opt.temp)

    if opt.press == 'dummy':
        press = DummyP()
    else:
        press = Manometer(opt.press)

    # temp = DummyFile('./test/Ar_filling_111220.out', -2)
    # press = DummyFile('./test/Ar_filling_111220.out', -1)

    app = QtWidgets.QApplication(sys.argv)
    ui = MainUI(temp, press, opt.output, opt.dt)
    ui.show()
    sys.exit(app.exec_())
