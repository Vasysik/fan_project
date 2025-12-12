import pytest
from rpi_daemon import update_fan_logic

def test_interval_mode_high():
    fan = {
        'mode': 'interval',
        'state': False,
        'params': {'temp_high': 60, 'temp_low': 45}
    }
    assert update_fan_logic(fan, 61.0) is True

def test_interval_mode_low():
    fan = {
        'mode': 'interval',
        'state': True,
        'params': {'temp_high': 60, 'temp_low': 45}
    }
    assert update_fan_logic(fan, 40.0) is False

def test_target_mode_high():
    fan = {
        'mode': 'target',
        'state': False,
        'params': {"target_temp": 50}
    }
    assert update_fan_logic(fan, 61.0) is True

def test_target_mode_low():
    fan = {
        'mode': 'target',
        'state': True,
        'params': {"target_temp": 50}
    }
    assert update_fan_logic(fan, 40.0) is False

def test_manual_mode():
    fan = {
        'mode': 'manual',
        'state': False,
        'params': {'manual_state': True}
    }
    assert update_fan_logic(fan, 100.0) is True
