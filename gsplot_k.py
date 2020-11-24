#!/usr/bin/env python3
# 2020/11/22

import sys
import os
import argparse
import termios
import atexit
from select import select
from datetime import datetime
import serial
from pynput import keyboard

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


class device(object):
    '''A device'''
    
    def __init__(self, port):
        self.name = 'Device'
        self.port = serial.Serial(port, 9600, timeout=1.0)
        self.err = False

    def __str__(self):
        return(self.name + ': ' + str(self.port))

    def read(self):
        val = 0.0
        return val

class therm(device):
    '''Thermometer'''
    
    def __init__(self, port):
        self.name = 'Thermometer'
        self.port = serial.Serial(port, 9600, timeout=1.0)
        self.err = False

        self.port.write(b'T\r')
        
    def read(self):
        self.err = False

        self.port.write(b'T\r')
        self.port.reset_input_buffer()
        buf = self.port.read(15)
        
        datastr = str(buf).strip('b\'')
        if len(datastr):
            datastr = data.split()[1]
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
        self.name = 'Manometer'
        self.port = serial.Serial(port, 9600, timeout=1.0)
        self.err = False

        self.port.write(b'xQ,2\r')    # speed 2: 16000 cycles 1.0 s
                                      #       3:  8000 cycles 0.5 s 
        self.port.write(b'xU,0\r')    # units: mbar
        self.port.write(b'x*A,1.0\r') # send value every 1.0 s

    def read(self):
        self.err = False

        self.port.write(b'-*G\r')
        self.port.reset_input_buffer()
        buf = self.port.read(12)
        
        datastr = str(buf).strip('b\'')
        if len(datastr):
            datastr = datastr.split()[0]
            try:
                float(datastr)
                val = float(pstr)
            except ValueError:
                self.err = True
        else:
            self.err = True
        return val

class dummyT(device):

    def __init__(self, port):
        self.name = 'dummy T'
        self.port = port
        self.err = False
        
    def read(self):
        return 25.0 + np.random.random_sample() - 0.5

class dummyP(device):

    def __init__(self, port):
        self.name = 'dummy P'
        self.port = port
        self.err = False
        self.t0 = datetime.now().timestamp()
        
    def read(self):
        delt = datetime.now().timestamp() - self.t0
        tau = 60.0
        return (1013.0 * 2.718**(- delt / tau) + \
            50.0 * np.random.random_sample() - 25.0)

# ______________________________________

    
def getch():
    ch = sys.stdin.read(1) 
    return ch

def kbhit():
    dr, dw, de = select([sys.stdin], [], [], 0)
    return dr != []

def check_keyboard():
    global delay, maxpt, interrupt
    
    if kbhit():
        key = getch()
        print(key)
        if key == 'q':
            ans = input('stop? y/[n]: ')
            print(ans)
            if ans.lower() == 'y':
                interrupt = True
                print('stopping...')
        elif key == 'd':
            prompt = 'delay is {0:.1f} s, new delay : '.format(delay)
            newdel = input(prompt)
            print(newdel)
            try:
                float(newdel)
                delay = float(newdel)
            except ValueError:
                pass
        elif key == 'm':
            prompt = 'maxpt is {0:d}, new maxpt : '.format(maxpt)
            newmaxpt = input(prompt)
            print(newmaxpt)
            try:
                int(newmaxpt)
                maxpt = int(newmaxpt)
            except ValueError:
                pass        
        else:
            print('q - quit, d - change delay, m - max points to plot')

# ______________________________________

delay = 5.0
maxpt = 150
interrupt = False


def main():
    global delay, maxpt, interrupt
    
    parser = argparse.ArgumentParser(description ='Read T and p',
             formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-f', '--file', type=str,
                        help = "output file name")
    parser.add_argument('-d', '--delay', type=float, default=5.0,
                        help = "delay between measurements [s] (default 5.0)")
    parser.add_argument('-t', '--therm', type=str, default='/dev/ttyUSB0',
                        help = "thermometer port (default: /dev/ttyUSB0)")
    parser.add_argument('-p', '--press', type=str, default='/dev/ttyUSB1',
                        help = "pressure transducer port (default: /dev/ttyUSB1)")
    parser.add_argument('-e', '--exp', type=str, default='test',
                        help = "experiment name")
    parser.add_argument('-m', '--maxpt', type=int, default=150,
                        help = "max points to plot (default 150)")
    args = parser.parse_args()

    if args.file:
        fname = args.file
    else:
        fname = input('output file: ')
    
    if os.path.isfile(fname):
        ow = input('file exists, overwrite? y/[n]: ')
        if ow.lower() == 'y':
            pass
        else:
            sys.exit(0)

    delay = args.delay
    maxpt = args.maxpt
    
    #temp = therm(args.therm)
    temp = dummyT(args.therm)
    print(temp)
    #pres = press(args.press)
    pres = dummyP(args.press)
    print(pres)

    # set non-buffered keyboard input
    fd = sys.stdin.fileno()
    new_term = old_term = termios.tcgetattr(fd)
    new_term[3] = (new_term[3] & ~termios.ICANON & ~termios.ECHO)
    termios.tcsetattr(fd, termios.TCSAFLUSH, new_term)
    atexit.register(termios.tcsetattr, fd, termios.TCSAFLUSH, old_term)
    
    # initialize plot
    # plt.ion()

    gs_kw = dict(width_ratios=[1], height_ratios=[1, 2])
    fig, (axt, axp) = plt.subplots(ncols=1, nrows=2, sharex=True,
                                   constrained_layout=True, gridspec_kw=gs_kw)

    fig.add_gridspec(nrows=2, ncols=1, height_ratios=[1, 2])
    fig.suptitle(fname)
    axp.xaxis.set_tick_params(rotation=30, labelsize=10)
    
    xs = []
    ts = []
    ps = []
    
    with open(fname, 'w', buffering=1) as f:
        print('writing to {0:s} every {1:.1f} s'.format(fname, args.delay))
        print('q - quit, d - change delay, m - max points to plot')

        f.write('# ' + args.exp + '\n')
        
        interrupt = False
        i = 0
        while not interrupt:
            i += 1
            if not i % 20:
                print('q - quit, d - change delay, m - max points to plot')

            tval = temp.read()
            pval = pres.read()
            
            tstart = datetime.now()            
            tstamp = tstart.strftime('%Y-%m-%d %H:%M:%S')

            if temp.err and pres.err:
                outstr = '      Error     Error'
            elif temp.err and not pres.err:
                outstr = '      Error {0:9.2f}'.format(pval)
            elif not temp.err and pres.err:
                outstr = '  {0:9.3f}     Error'.format(tval)
            else:
                outstr = '  {0:9.3f} {1:9.2f}'.format(tval, pval)
                f.write(tstamp + outstr + '\n')

            print(tstamp + outstr)
            xs.append(mdates.date2num(tstart))
            
            if not temp.err:
                ts.append(tval)
            else:
                ts.append(ts[-1])
            if not pres.err:
                ps.append(pval)
            else:
                ps.append(ps[-1])

            if len(xs) > maxpt:
                xs = xs[-maxpt:]
                ts = ts[-maxpt:]
                ps = ps[-maxpt:]
                
            axt.cla()
            axp.cla()
            axt.set_ylabel('T / C')        
            axp.set_ylabel('P / mbar')
            axt.grid(b=True, which='major', linestyle='--')
            axp.grid(b=True, which='major', linestyle='--')
            tt = axt.text(0.85, 0.8, '         ', transform=axt.transAxes)
            tp = axp.text(0.85, 0.9, '         ', transform=axp.transAxes)
            tt.set_text('{0:9.3f}'.format(tval))
            tp.set_text('{0:9.2f}'.format(pval))
            axt.plot_date(xs, ts, 'ro-', linewidth=0.5, markersize=1.5)
            axp.plot_date(xs, ps, 'bo-', linewidth=0.5, markersize=1.5)
            # plt.draw()

            check_keyboard()

            plt.pause(delay)

    print('data saved to ' + fname)
    termios.tcsetattr(fd, termios.TCSAFLUSH, old_term)
    print('close plot window to exit')    
    plt.show(block=True)

if __name__ == '__main__':
    main()

