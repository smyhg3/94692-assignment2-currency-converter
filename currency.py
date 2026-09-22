"""Currency calculations, independent of HTTP and the user interface."""

import math


def _validate_number(value, name):
    """Require a finite Python int or float, excluding booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{name} must be a finite number.")


def _validate_rate(exchange_rate):
    _validate_number(exchange_rate, "Exchange rate")
    if exchange_rate <= 0:
        raise ValueError("Exchange rate must be greater than zero.")


def validate_amount(amount):
    """Reject negative or non-finite amounts; zero is allowed."""
    _validate_number(amount, "Amount")
    if amount < 0:
        raise ValueError("Amount must not be negative.")


def convert_amount(amount, exchange_rate):
    """Convert a non-negative amount without rounding the result."""
    validate_amount(amount)
    _validate_rate(exchange_rate)
    result = amount * exchange_rate
    _validate_number(result, "Converted amount")
    return result


def inverse_rate(exchange_rate):
    """Return the reciprocal of a positive, finite exchange rate."""
    _validate_rate(exchange_rate)
    result = 1 / exchange_rate
    _validate_rate(result)
    return result
