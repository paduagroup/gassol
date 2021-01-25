#!/usr/bin/env python3

import sys
from PyQt5 import QtWidgets
from qtgassol.ui import MainUI
from qtgassol.device import dummyT, dummyP


def main():
    temp = dummyT()
    pres = dummyP()

    app = QtWidgets.QApplication(sys.argv)
    ui = MainUI(temp, pres, 'output.txt', 1.0)
    ui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
