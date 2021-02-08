from PyQt5 import QtGui, QtCore, QtWidgets
from datetime import datetime
import time
import numpy as np
import pyqtgraph as pg
from .timeseries import detect_anomaly_t, detect_anomaly_p


class MainUI(QtWidgets.QMainWindow):
    def __init__(self, temp, pres, output, interval):
        super().__init__()
        self.setWindowTitle('GasSol')
        self.resize(1000, 1000)

        # devices
        self.temp = temp
        self.pres = pres

        # top-level widget
        self.widget = QtWidgets.QWidget()
        self.setCentralWidget(self.widget)

        # widgets
        self.lab_file = QtWidgets.QLabel('Log file')
        self.inp_file = QtWidgets.QLineEdit(output)
        self.btn_start = QtWidgets.QPushButton('Start')
        self.btn_pause = QtWidgets.QPushButton('Pause')
        self.btn_pause.setDisabled(True)
        self.lab_interval = QtWidgets.QLabel('Interval (s)')
        self.inp_interval = QtWidgets.QLineEdit(str(interval))
        self.btn_interval = QtWidgets.QPushButton('Update')
        self.text = QtWidgets.QTextEdit()
        self.text.setText('%-20s %10s %10s' % ('# Date Time', 'T(C)', 'P(mPa)'))

        self.lab_average = QtWidgets.QLabel('Averages for temperature and pressure')
        self.text_t = QtWidgets.QLineEdit()
        self.text_p = QtWidgets.QLineEdit()

        self.lab_temp = QtWidgets.QLabel('Target temperature (C)')
        self.inp_temp = QtWidgets.QLineEdit('To be implemented')
        self.btn_temp = QtWidgets.QPushButton('Update')
        self.inp_temp.setDisabled(True)
        self.btn_temp.setDisabled(True)

        # plots
        self.plt_widget = pg.GraphicsLayoutWidget()
        self.plt1 = self.plt_widget.addPlot()
        self.plt1.setLabel('left', 'T / C')
        self.plt1.setAxisItems({'bottom': pg.DateAxisItem()})
        self.plt1.showGrid(x=True, y=True, alpha=0.5)
        self.plt_widget.nextRow()
        self.plt2 = self.plt_widget.addPlot()
        self.plt2.setLabel('left', 'P / mPa')
        self.plt2.setAxisItems({'bottom': pg.DateAxisItem()})
        self.plt2.setXLink(self.plt1)  # share X axis scales
        self.plt2.showGrid(x=True, y=True, alpha=0.5)
        self.curve1 = self.plt1.plot(symbolBrush=(0, 0, 255), symbolSize=8)
        self.curve2 = self.plt2.plot(symbolBrush=(0, 0, 255), symbolSize=8)
        self.curve1_anomaly = self.plt1.scatterPlot(symbolBrush=(255, 0, 0), symbolSize=16)
        self.curve2_anomaly = self.plt2.scatterPlot(symbolBrush=(255, 0, 0), symbolSize=16)

        # select region in plot
        timestamp = time.time()
        self.region = pg.LinearRegionItem([timestamp, timestamp + 30],
                                          movable=False, span=[0.0, 0.2], swapMode='block')
        self.plt1.addItem(self.region)

        # layout
        layout = QtWidgets.QHBoxLayout()
        self.widget.setLayout(layout)

        l_left = QtWidgets.QVBoxLayout()
        layout.addLayout(l_left, stretch=0)
        layout.addWidget(self.plt_widget, stretch=1)

        l = QtWidgets.QHBoxLayout()
        l.addWidget(self.lab_file)
        l.addWidget(self.inp_file)
        l_left.addLayout(l)

        l = QtWidgets.QHBoxLayout()
        l.addWidget(self.btn_start)
        l.addWidget(self.btn_pause)
        l_left.addLayout(l)

        l = QtWidgets.QHBoxLayout()
        l.addWidget(self.lab_interval)
        l.addWidget(self.inp_interval)
        l.addWidget(self.btn_interval)
        l_left.addLayout(l)

        l_left.addWidget(self.text)
        self.text.setMinimumWidth(350)

        l = QtWidgets.QHBoxLayout()
        l.addWidget(self.lab_temp)
        l.addWidget(self.inp_temp)
        l.addWidget(self.btn_temp)
        l_left.addLayout(l)

        l_left.addWidget(self.lab_average)
        l_left.addWidget(self.text_t)
        l_left.addWidget(self.text_p)

        # data
        self.time_list = []
        self.t_list = []
        self.p_list = []

        # timer for update data
        self.timer = QtCore.QTimer(self)

        # listeners
        self._add_listeners()

        self._is_running = False

    def _add_listeners(self):
        self.timer.timeout.connect(self.step)
        self.btn_start.clicked.connect(self.start)
        self.btn_pause.clicked.connect(self.pause)
        self.btn_interval.clicked.connect(self.set_interval)
        self.btn_temp.clicked.connect(self.set_temperature)
        self.region.sigRegionChangeFinished.connect(self.calc_average)

    def step(self):
        timestamp = time.time()
        t = self.temp.read()
        p = self.pres.read()
        string = '%-20s %10.3f %10.2f' % (datetime.fromtimestamp(timestamp).strftime('%y-%m-%d %H:%M:%S'), t, p)
        self.text.append(string)

        self._file.write(string + '\n')

        self.time_list.append(timestamp)
        self.t_list.append(t)
        self.p_list.append(p)
        self.curve1.setData(self.time_list, self.t_list)
        self.curve2.setData(self.time_list, self.p_list)

        self.region.setBounds([self.time_list[0], max(timestamp, self.time_list[0] + 30)])
        self.region.setMovable(True)

    def calc_average(self):
        '''
        calculate the average under selected region
        '''
        bound = self.region.getRegion()
        time_array_crude = np.array(self.time_list)
        idx = np.where((time_array_crude > bound[0] - 0.001) & (time_array_crude < bound[1] + 0.001))[0]
        n = len(idx)
        time_array = time_array_crude[idx]
        t_array = np.array(self.t_list)[idx]
        p_array = np.array(self.p_list)[idx]

        idx_anomaly_t = [i for i in range(2, n - 2) if
                         detect_anomaly_t(t_array[[i - 2, i - 1, i + 1, i + 2]], t_array[i])]
        idx_anomaly_p = [i for i in range(2, n - 2) if
                         detect_anomaly_p(p_array[[i - 2, i - 1, i + 1, i + 2]], p_array[i])]

        self.curve1_anomaly.setData(time_array[idx_anomaly_t], t_array[idx_anomaly_t])
        self.curve2_anomaly.setData(time_array[idx_anomaly_p], p_array[idx_anomaly_p])

        mask = np.ones(n, np.bool)
        mask[idx_anomaly_t] = 0
        t_array_valid = t_array[mask]

        mask = np.ones(n, np.bool)
        mask[idx_anomaly_p] = 0
        p_array_valid = p_array[mask]

        if len(t_array_valid) > 0:
            t_ave = np.mean(t_array_valid)
            t_std = np.std(t_array_valid)
        else:
            t_ave = t_std = -1
        if len(p_array_valid) > 0:
            p_ave = np.mean(p_array_valid)
            p_std = np.std(p_array_valid)
        else:
            p_ave = p_std = -1

        self.text_t.setText('T: %10.3f +- %10.4f' % (t_ave, t_std))
        self.text_p.setText('P: %10.2f +- %10.3f' % (p_ave, p_std))

    def set_interval(self):
        try:
            interval = float(self.inp_interval.text())
        except ValueError:
            return False
        else:
            self.timer.setInterval(interval * 1000)
            return True

    def set_temperature(self):
        '''
        TODO
        '''
        try:
            temp = float(self.inp_temp.text())
        except ValueError:
            return False
        else:
            return True

    def start(self):
        if self._is_running:
            return
        if not self.set_interval():
            return

        try:
            self._file = open(self.inp_file.text(), 'a')
        except:
            return

        self._file.write('# File opened at %s\n' % datetime.now())

        self.step()
        self.timer.start()
        self._is_running = True

        self.btn_start.setDisabled(True)
        self.btn_pause.setDisabled(False)

    def pause(self):
        '''
        Pause and close the output file
        '''
        if not self._is_running:
            return

        self.timer.stop()
        self._is_running = False
        self._file.close()

        self.btn_start.setDisabled(False)
        self.btn_pause.setDisabled(True)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        '''
        Gracefully stop the application
        '''
        self.pause()
        event.accept()
