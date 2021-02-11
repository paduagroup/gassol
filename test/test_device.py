import pytest
from qtgassol.device import FlukeThermometer, GeManometer

if __name__ == '__main__':
    temp = FlukeThermometer.detect()
    if temp is not None:
        print(temp)
        print(temp.read())

    press = GeManometer.detect()
    if press is not None:
        print(press)
        print(press.read())
