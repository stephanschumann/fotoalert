import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from opportunity import _azimuth_zone, AzimuthZone

def test_front():
    assert _azimuth_zone(90, 85) == AzimuthZone.FRONT   # delta=5
    assert _azimuth_zone(90, 55) == AzimuthZone.FRONT   # delta=35 (Grenze)

def test_side():
    assert _azimuth_zone(90, 140) == AzimuthZone.SIDE   # delta=50
    assert _azimuth_zone(90, 0) == AzimuthZone.SIDE     # delta=90

def test_back():
    assert _azimuth_zone(270, 90) == AzimuthZone.BACK   # delta=180
    assert _azimuth_zone(235, 90) == AzimuthZone.BACK   # delta=145 (Grenze)

def test_wrap():
    assert _azimuth_zone(355, 5) == AzimuthZone.FRONT   # delta=10, Wrap
    assert _azimuth_zone(5, 355) == AzimuthZone.FRONT
