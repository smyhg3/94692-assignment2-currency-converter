"""Currency calculations and result formatting, independent of HTTP and Streamlit."""

import math


def _validate_number(value, name):
    """Require a finite Python int or float, excluding booleans."""
    # bool subclasses int, but True/False are not valid amounts or rates.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite:
        raise ValueError(f"{name} must be a finite number.")


def _validate_rate(exchange_rate):
    """Require a positive, finite numeric rate."""
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


def format_conversion_result(
    rate_date, from_currency, to_currency, rate, amount, converted_amount, inverse_rate
):
    """Format supplied values using the assignment wording without recalculating."""
    return (
        f"The conversion rate on {rate_date} from {from_currency} to {to_currency} "
        f"was {rate:.6g}. So {amount:,.2f} in {from_currency} correspond to "
        f"{converted_amount:,.2f} in {to_currency}. The inverse rate was {inverse_rate:.6g}."
    )
