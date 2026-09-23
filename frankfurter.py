"""Retrieve currencies and daily rates from the Frankfurter v1 API."""

from datetime import date
import math

from api import get_json


BASE_URL = "https://api.frankfurter.dev/v1"


def _currency_code(code):
    """Normalize a three-letter currency code."""
    if not isinstance(code, str):
        raise ValueError("Currency code must be a string.")
    code = code.strip().upper()
    if len(code) != 3 or not code.isascii() or not code.isalpha():
        raise ValueError("Currency code must contain three ASCII letters.")
    return code


def get_currencies():
    """Return a dictionary mapping supported currency codes to names."""
    data = get_json(f"{BASE_URL}/currencies")
    if not isinstance(data, dict) or not data:
        raise RuntimeError("Frankfurter returned an invalid currency list.")
    for code, name in data.items():
        if not isinstance(name, str) or not name.strip():
            raise RuntimeError("Frankfurter returned an invalid currency name.")
        try:
            if _currency_code(code) != code:
                raise ValueError("Non-standard currency code.")
        except ValueError as error:
            raise RuntimeError("Frankfurter returned an invalid code.") from error
    return data


def _get_rate(endpoint, from_currency, to_currency):
    """Fetch a rate and retain the actual publication date."""
    base = _currency_code(from_currency)
    target = _currency_code(to_currency)
    if base == target:
        raise ValueError("Choose two different currencies.")
    data = get_json(
        f"{BASE_URL}/{endpoint}",
        params={"base": base, "symbols": target},
    )
    try:
        rate = data["rates"][target]
        rate_date = data["date"]
        published_date = date.fromisoformat(rate_date)
        requested_date = date.today() if endpoint == "latest" else date.fromisoformat(endpoint)
        if published_date.isoformat() != rate_date or published_date > requested_date:
            raise ValueError("Unexpected publication date.")
        if data["base"] != base:
            raise ValueError("Unexpected base currency.")
        if isinstance(rate, bool) or not isinstance(rate, (int, float)):
            raise ValueError("Rate is not numeric.")
        if not math.isfinite(rate) or rate <= 0:
            raise ValueError("Rate must be positive and finite.")
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise RuntimeError("Frankfurter returned missing or invalid exchange-rate data. Please try another date or try again later.") from error
    return {"date": rate_date, "base": base, "target": target, "rate": rate}


def get_latest_rate(from_currency, to_currency):
    """Return the latest available rate and its publication date."""
    return _get_rate("latest", from_currency, to_currency)


def get_historical_rate(from_currency, to_currency, historical_date):
    """Retrieve a rate for a YYYY-MM-DD date, possibly an earlier workday."""
    if not isinstance(historical_date, str):
        raise ValueError("Historical date must be a YYYY-MM-DD string.")
    try:
        parsed_date = date.fromisoformat(historical_date)
    except ValueError as error:
        raise ValueError("Historical date must be a valid YYYY-MM-DD date.") from error
    if parsed_date.isoformat() != historical_date:
        raise ValueError("Historical date must use YYYY-MM-DD format.")
    if parsed_date > date.today():
        raise ValueError("Historical date must not be in the future.")
    return _get_rate(historical_date, from_currency, to_currency)


def get_three_year_rates(from_currency, to_currency):
    """Return sorted Date/Rate records for the last three calendar years."""
    base = _currency_code(from_currency)
    target = _currency_code(to_currency)
    if base == target:
        raise ValueError("Choose two different currencies.")
    end = date.today()
    try:
        start = end.replace(year=end.year - 3)
    except ValueError:
        # February 29 becomes February 28 in a non-leap year.
        start = end.replace(year=end.year - 3, day=28)
    data = get_json(
        f"{BASE_URL}/{start.isoformat()}..{end.isoformat()}",
        params={"base": base, "symbols": target},
    )
    try:
        if data["base"] != base or not isinstance(data["rates"], dict):
            raise ValueError("Unexpected time-series response.")
        records = []
        for day, rates in data["rates"].items():
            published = date.fromisoformat(day)
            if published.isoformat() != day or published > end:
                raise ValueError("Invalid publication date.")
            rate = rates[target]
            if isinstance(rate, bool) or not isinstance(rate, (int, float)):
                raise ValueError("Rate is not numeric.")
            if not math.isfinite(rate) or rate <= 0:
                raise ValueError("Rate must be positive and finite.")
            # The API can include a previous working day before the start.
            if published >= start:
                records.append({"Date": published, "Rate": rate})
        if not records:
            raise ValueError("No rates in the requested period.")
    except (KeyError, TypeError, ValueError, OverflowError) as error:
        raise RuntimeError("Three-year trend data is unavailable or invalid. Please try again later.") from error
    return sorted(records, key=lambda record: record["Date"])
