from typing import Literal

LengthUnit = Literal["m", "km", "cm", "mm"]
WeightUnit = Literal["g", "kg"]

# base units: meter, gram

_LENGTH_TO_M = {
    "km": 1000.0,
    "m": 1.0,
    "cm": 0.01,
    "mm": 0.001,
}

_WEIGHT_TO_G = {
    "kg": 1000.0,
    "g": 1.0,
}

def convert_length(value: float, from_u: LengthUnit, to_u: LengthUnit) -> float:
    if value is None or from_u not in _LENGTH_TO_M or to_u not in _LENGTH_TO_M:
        raise ValueError("invalid length conversion")
    # absolute zero analogy doesn't apply to length, but disallow NaN
    if value != value:  # NaN check
        raise ValueError("value is NaN")
    # to meters
    meters = value / _LENGTH_TO_M[from_u]
    # to target
    return meters / _LENGTH_TO_M[to_u]

def convert_weight(value: float, from_u: WeightUnit, to_u: WeightUnit) -> float:
    if value is None or from_u not in _WEIGHT_TO_G or to_u not in _WEIGHT_TO_G:
        raise ValueError("invalid weight conversion")
    if value != value:
        raise ValueError("value is NaN")
    grams = value * _WEIGHT_TO_G[from_u]
    return grams / _WEIGHT_TO_G[to_u]
