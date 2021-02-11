import time
import pytest
from qtgassol.device import FlukeThermometer, GeManometer, Thermostat, HuberThermostat


def test_temp():
    temp = FlukeThermometer.detect()
    if temp is not None:
        print(temp)
        print(temp.read())


def test_press():
    press = GeManometer.detect()
    if press is not None:
        print(press)
        print(press.read())


def test_thermo():
    stat = HuberThermostat.detect()
    if stat is not None:
        print(stat)
        print(stat.read())


def test_thermo_preset():
    thermo = Thermostat(None)
    assert thermo.preset('30')
    assert thermo.get_preset(time.time() - 10) == 30
    assert thermo.get_preset(time.time() + 10) == 30
    assert thermo.get_preset() == 30

    assert thermo.preset('30, 10, 50')
    assert thermo.get_preset(time.time() - 10) == 30
    assert thermo.get_preset(time.time() + 10 * 60) == 50
    assert thermo.get_preset(time.time() + 20 * 60) == 50
    assert pytest.approx(thermo.get_preset()) == 30
    assert pytest.approx(thermo.get_preset(time.time() + 2 * 60)) == 34

    assert thermo.preset('30, 10, 50; 20, 30')
    assert pytest.approx(thermo.get_preset(time.time() - 10)) == 30
    assert pytest.approx(thermo.get_preset(time.time() + 10 * 60), abs=0.001) == 50
    assert pytest.approx(thermo.get_preset(time.time() + 30 * 60)) == 30
    assert pytest.approx(thermo.get_preset(time.time() + 40 * 60)) == 30
    assert pytest.approx(thermo.get_preset()) == 30
    assert pytest.approx(thermo.get_preset(time.time() + 2 * 60)) == 34
    assert pytest.approx(thermo.get_preset(time.time() + 20 * 60)) == 40

    assert thermo.preset('30, 10, 50; 20, 30; 2, 0')
    assert pytest.approx(thermo.get_preset(time.time() - 10)) == 30
    assert pytest.approx(thermo.get_preset(time.time() + 10 * 60), abs=0.001) == 50
    assert pytest.approx(thermo.get_preset(time.time() + 30 * 60), abs=0.001) == 30
    assert pytest.approx(thermo.get_preset(time.time() + 40 * 60)) == 0
    assert pytest.approx(thermo.get_preset()) == 30
    assert pytest.approx(thermo.get_preset(time.time() + 2 * 60)) == 34
    assert pytest.approx(thermo.get_preset(time.time() + 20 * 60)) == 40
    assert pytest.approx(thermo.get_preset(time.time() + 31 * 60), abs=0.001) == 15
