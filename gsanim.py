#!/usr/bin/env python3

import datetime as dt
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as dates
from matplotlib.animation import FuncAnimation
from matplotlib.widgets import Button, TextBox 


class device(object):
    '''A device'''
    
    def __init__(self, port):
        self.port = port

    def __str__(self):
        return('Port: ' + port)

    def measure():
        return 0.0
        

class therm(device):
    '''The thermometer'''
    
    def measure(self):
        return 25.0 + 1.0 * (np.random.random_sample() - 0.5)

class manom(device):
    '''The manometer'''
    
    def measure(self):
        return 100.0 + 10.0 * (np.random.random_sample() - 0.5)

#_______________________________________

class gsplot(object):
    """Plot temperature and pressure in gas solubility experiment"""

    def __init__(self):

        self.temp = therm('COM5')
        self.pres = manom('COM6')

        self.interval = 2000              # ms
        self.ani = None
        self.fout = None

        self.xs, self.ts, self.ps = [], [], []
        
        gs_kw = dict(width_ratios=[1], height_ratios=[1, 2])
        self.fig, (self.axt, self.axp) = plt.subplots(nrows=2, sharex=True, gridspec_kw=gs_kw)
        self.tplot, = self.axt.plot_date([], [], 'ro-', linewidth=0.5, markersize=1.5)
        self.pplot, = self.axp.plot_date([], [], 'bo-', linewidth=0.5, markersize=1.5)

        # self.fig.suptitle(outfile)
        self.fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1, 2])
        plt.subplots_adjust(left=0.12, bottom=0.14, top=0.88, hspace=0.1)

        # axes
        tstamp = dt.datetime.now()
        self.xlo = dates.date2num(tstamp)
        #self.xhi = dates.date2num(tstamp + dt.timedelta(seconds=30))
        self.xhi = self.xlo + 60.0/86400
        self.plo, self.phi = 950.0, 1050.0
        self.tlo, self.thi = 20.0, 30.0        
        self.axt.set_xlim(self.xlo, self.xhi)
        self.axt.set_ylim(self.tlo, self.thi)
        self.axp.set_ylim(self.plo, self.phi)

        self.axp.xaxis.set_tick_params(rotation=45, labelsize=10)
        self.axt.set_ylabel('T / C')
        self.axp.set_ylabel('P / mbar')
        self.axt.grid(b=True, which='major', linestyle='--')
        self.axp.grid(b=True, which='major', linestyle='--')

        self.tt = self.axt.text(0.8, 0.8, '         ', transform=self.axt.transAxes)
        self.tp = self.axp.text(0.8, 0.9, '         ', transform=self.axp.transAxes)
        
        # widgets
        topline = 0.9
        height = 0.05
        
        axfile = plt.axes([0.12, topline, 0.28, height])
        self.wfile = TextBox(axfile, 'File ', initial='')
        axclose = plt.axes([0.41, topline, 0.09, height])
        self.wclose = Button(axclose, 'Close')

        axdelay = plt.axes([0.6, topline, 0.07, height])
        self.wdelay = TextBox(axdelay, 'Delay ', initial=str(self.interval/1000.))
        axstart = plt.axes([0.71, topline, 0.09, height])
        self.wstart = Button(axstart, 'Start', color=(0.3, 1.0, 0.3), hovercolor=(0.6, 1.0, 0.6))
        axstop = plt.axes([0.81, topline, 0.09, height])
        self.wstop = Button(axstop, 'Stop', color=(1.0, 0.3, 0.3), hovercolor=(1.0, 0.6, 0.6))

        self.startgui()


    def setfile(self, event):
        try:
            self.fout = open(event, 'a')
        except OSError:
            print('cannot open ', event)

    def closefile(self, event=None):
        if self.fout and not self.fout.closed:
            self.fout.close()
            self.fout = None
            self.wfile.set_val('')

    def setdelay(self, event):
        try:
            delay = float(event)
            print('delay {0:4.1f} s'.format(delay))
            self.interval = 1000 * delay
        except ValueError:
            pass

    def stoprun(self, event=None):
        if self.ani is not None:
            self.ani._stop()
            self.ani = None

    def startrun(self, event=None):
        if self.ani is None:
            self.ani = FuncAnimation(self.fig, self.run, interval=self.interval, repeat=False, blit=False, save_count=0)
            plt.show()
            
    def run(self, frame):
        t = self.temp.measure()
        p = self.pres.measure()

        tstamp = dt.datetime.now()
        readstr = tstamp.strftime('%Y-%m-%d %H:%M:%S') + '  {0:9.3f} {1:9.2f}'.format(t, p)
        if self.fout and not self.fout.closed:
            self.fout.write(readstr + '\n')
        x = dates.date2num(tstamp)
        self.xs.append(x)
        self.ts.append(t)
        self.ps.append(p)

        if len(self.xs) > 30:
            self.xs.pop(0)
            self.ts.pop(0)
            self.ps.pop(0)
            self.xhi = self.xs[-1] + 10.0/86400

        self.xlo = self.xs[0]
        if t < self.tlo or t > self.tlo + 2.0:
            self.tlo = t - 2.0
        if t > self.thi or t < self.thi - 2.0:
            self.thi = t + 2.0
        if p < self.plo or p > self.plo + 10.0:
            self.plo = p - 10.0
        if p > self.phi or p < self.phi - 10.0:
            self.phi = p + 10.0
        self.axt.set_xlim(self.xlo, self.xhi)
        self.axt.set_ylim(self.tlo, self.thi)
        self.axp.set_ylim(self.plo, self.phi)

        self.tplot.set_data(self.xs, self.ts)
        self.pplot.set_data(self.xs, self.ps)

        self.tt.set_text('{0:9.3f}'.format(t))
        self.tp.set_text('{0:9.2f}'.format(p))

        return self.tplot, self.pplot

    def startgui(self):
        # self.ani = FuncAnimation(self.fig, self.run, interval=self.interval, repeat=False, blit=False, save_count=0, cache_frame_data=False)
        self.wfile.on_submit(self.setfile)
        self.wclose.on_clicked(self.closefile)
        self.wdelay.on_submit(self.setdelay)
        self.wstart.on_clicked(self.startrun)
        self.wstop.on_clicked(self.stoprun)
        plt.show()
        
        
def main():
    pt = gsplot()
    pt.closefile()

if __name__ == '__main__':
    main()
