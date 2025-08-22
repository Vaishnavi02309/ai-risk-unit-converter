from src.unit_converter import convert_length, convert_weight
import math

def approx(a, b, eps=1e-9): return abs(a - b) < eps

def test_length_basic():
    assert approx(convert_length(1, "km", "m"), 1000)
    assert approx(convert_length(150, "cm", "m"), 1.5)
    assert approx(convert_length(10, "mm", "cm"), 1.0)

def test_length_identity():
    assert approx(convert_length(42.5, "m", "m"), 42.5)

def test_weight_basic():
    assert approx(convert_weight(1, "kg", "g"), 1000)
    assert approx(convert_weight(250, "g", "kg"), 0.25)

def test_invalid_units():
    import pytest
    with pytest.raises(ValueError):
        convert_length(1, "mile", "m")   # invalid
    with pytest.raises(ValueError):
        convert_weight(1, "lb", "kg")    # invalid

def test_nan_rejected():
    import pytest
    with pytest.raises(ValueError):
        convert_length(math.nan, "m", "cm")
    with pytest.raises(ValueError):
        convert_weight(float("nan"), "g", "kg")
