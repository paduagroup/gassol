from PyQt5 import QtGui, QtCore, QtWidgets
from datetime import datetime
import time
import numpy as np
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
        self.lab_interval = QtWidgets.QLabel('Interval (s)')
        self.inp_interval = QtWidgets.QLineEdit(str(interval))
        self.btn_interval = QtWidgets.QPushButton('Update interval')
        self.text = QtWidgets.QTextEdit()
        self.text.setText('%15s %12s %12s' % ('Time', 'T(C)', 'P(mPa)'))

        self.text_t = QtWidgets.QLineEdit()
        self.text_p = QtWidgets.QLineEdit()

        # plots
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

        # select region in plot
        self._init_timestamp = time.time()
        self.region = pg.LinearRegionItem([self._init_timestamp, self._init_timestamp + 10],
                                          movable=False, span=[0.0, 0.2], swapMode='block')
        self.plt1.addItem(self.region)

        # layout
        self.layout = QtWidgets.QHBoxLayout()
        self.l_left = QtWidgets.QVBoxLayout()
        self.layout.addLayout(self.l_left)
        self.layout.addWidget(self.plt_widget)

        self.l_left.addWidget(self.lab_file)
        self.l_left.addWidget(self.inp_file)
        self.l_left.addWidget(self.btn_start)
        self.l_left.addWidget(self.btn_pause)
        self.l_left.addWidget(self.lab_interval)
        self.l_left.addWidget(self.inp_interval)
        self.l_left.addWidget(self.btn_interval)
        self.l_left.addWidget(self.text, stretch=True)
        self.l_left.addWidget(self.text_t)
        self.l_left.addWidget(self.text_p)

        self.widget.setLayout(self.layout)

        # listeners
        self._add_listeners()

        # data
        self.time_list = []
        self.t_list = []
        self.p_list = []

        # timer for update data
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.run_timer)

        self._output = output
        self._is_running = False

    def _add_listeners(self):
        self.btn_start.clicked.connect(self.start)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_interval.clicked.connect(self.set_interval)
        self.region.sigRegionChangeFinished.connect(self.average)
        self.plt1.sigXRangeChanged.connect(self.sync_range)

    def run_timer(self):
        timestamp = time.time()
        t = self.temp.read()
        p = self.pres.read()
        string = '%-15s %-12.3f %-12.3f' % (datetime.fromtimestamp(timestamp).strftime('%dT%H:%M:%S'), t, p)
        self.text.append(string)

        self._file.write(string + '\n')

        self.time_list.append(timestamp)
        self.t_list.append(t)
        self.p_list.append(p)
        self.curve1.setData(self.time_list, self.t_list)
        self.curve2.setData(self.time_list, self.p_list)

        self.region.setBounds([self._init_timestamp, timestamp])
        self.region.setMovable(True)

    def sync_range(self):
        self.plt2.blockSignals(True)
        self.plt2.setRange(xRange=self.plt1.getAxis('bottom').range)
        self.plt2.blockSignals(False)

    def average(self):
        '''
        calculate the average under selected region
        '''
        bound = self.region.getRegion()
        t_l = []
        p_l = []
        for i, (time, t, p) in enumerate(zip(self.time_list, self.t_list, self.p_list)):
            if time > bound[0] and time < bound[1]:
                t_l.append(t)
                p_l.append(p)
        if len(t_l) > 0:
            t_ave = np.mean(t_l)
            t_std = np.std(t_l)
        else:
            t_ave = t_std = 0
        if len(p_l) > 0:
            p_ave = np.mean(p_l)
            p_std = np.std(p_l)
        else:
            p_ave = p_std = 0
        self.text_t.setText('T: %f +- %f' % (t_ave, t_std))
        self.text_p.setText('P: %f += %f' % (p_ave, p_std))

    def set_interval(self):
        try:
            interval = float(self.inp_interval.text())
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
