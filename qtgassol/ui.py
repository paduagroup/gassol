from PyQt5 import QtGui, QtCore, QtWidgets
from datetime import datetime
import time
import pyqtgraph as pg


class MainUI(QtWidgets.QMainWindow):
    def __init__(self, temp, pres, output, interval):
        super().__init__()
        self.setWindowTitle('GasSol')
        self.setMinimumSize(1000, 1000)

        # devices
        self.temp = temp
        self.pres = pres

        # top-level widget
        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)

        # widgets
        self.lab_file = QtWidgets.QLabel('Filename')
        self.inp_file = QtWidgets.QLineEdit(output)
        self.btn_start = QtWidgets.QPushButton('Start')
        self.btn_pause = QtWidgets.QPushButton('Pause')
        self.label = QtWidgets.QLabel('Interval (s)')
        self.input = QtWidgets.QLineEdit(str(interval))
        self.button = QtWidgets.QPushButton('Update interval')
        self.text = QtWidgets.QTextEdit()
        self.text.setText('%15s %12s %12s' % ('Time', 'T(C)', 'P(mPa)'))

        self.plt_widget = pg.GraphicsLayoutWidget()
        self.plt1 = self.plt_widget.addPlot()
        self.plt1.setLabel('left', 'T / C')
        self.plt1.setAxisItems({'bottom': pg.DateAxisItem()})
        self.plt_widget.nextRow()
        self.plt2 = self.plt_widget.addPlot()
        self.plt2.setLabel('left', 'P / mPa')
        self.plt2.setAxisItems({'bottom': pg.DateAxisItem()})
        self.curve1 = self.plt1.plot()
        self.curve2 = self.plt2.plot()

        # layout
        self.layout = QtWidgets.QGridLayout()
        self.widget.setLayout(self.layout)

        self.layout.addWidget(self.lab_file, 0, 0)
        self.layout.addWidget(self.inp_file, 0, 1)
        self.layout.addWidget(self.btn_start, 0, 2)
        self.layout.addWidget(self.btn_pause, 0, 3)
        self.layout.addWidget(self.label, 1, 0)
        self.layout.addWidget(self.input, 1, 1)
        self.layout.addWidget(self.button, 2, 0, 1, 2)
        self.layout.addWidget(self.text, 3, 0, 1, 2)
        self.layout.addWidget(self.plt_widget, 1, 2, 3, 2)

        # listeners
        self.btn_start.clicked.connect(self.start)
        self.btn_pause.clicked.connect(self.pause)
        self.button.clicked.connect(self.set_interval)

        # data
        self.time_list = []
        self.t_list = []
        self.p_list = []

        # timer for update data
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.run_timer)

        self._output = output
        self._is_running = False

    def get_data(self):
        t = self.temp.read()
        p = self.pres.read()
        return t, p

    def run_timer(self):
        timestamp = time.time()
        t, p = self.get_data()
        string = '%-15s %-12.3f %-12.3f' % (datetime.fromtimestamp(timestamp).strftime('%dT%H:%M:%S'), t, p)
        self.text.append(string)

        self._file.write(string + '\n')

        self.time_list.append(timestamp)
        self.t_list.append(t)
        self.p_list.append(p)
        self.curve1.setData(self.time_list, self.t_list)
        self.curve2.setData(self.time_list, self.p_list)

    def set_interval(self):
        try:
            interval = float(self.input.text())
        except ValueError:
            return False
        else:
            self.timer.setInterval(interval * 1000)
            return True

    def start(self):
        if self._is_running:
            return
        if not self.set_interval():
            return

        try:
            self._file = open(self._output, 'a')
        except:
            return

        self._file.write('File opened at %s\n' % datetime.now())

        self.timer.start()
        self._is_running = True

    def pause(self):
        '''
        Pause and close the output file
        '''
        if not self._is_running:
            return

        self.timer.stop()
        self._is_running = False
        self._file.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        '''
        Gracefully stop the application
        '''
        self.pause()
        event.accept()
