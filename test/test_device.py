import pytest
from qtgassol.device import Thermometer, Manometer

if __name__ == '__main__':
    temp = Thermometer.detect()
    if temp is not None:
        print(temp)
        print(temp.read())

    press = Manometer.detect()
    if press is not None:
        print(press)
        print(press.read())
