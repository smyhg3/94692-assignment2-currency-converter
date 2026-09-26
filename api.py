"""Generic HTTP helpers for JSON APIs."""

import requests


def get_url(url):
    """Return the HTTP status and response text for the template interface."""
    response = requests.get(url, timeout=10)
    return response.status_code, response.text


def get_json(url, params=None):
    """GET a URL with optional query parameters; return JSON or raise RuntimeError."""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.Timeout as error:
        raise RuntimeError("The exchange-rate service timed out. Please try again.") from error
    except requests.ConnectionError as error:
        raise RuntimeError("Cannot connect to the exchange-rate service. Check your internet connection and try again.") from error
    except requests.HTTPError as error:
        raise RuntimeError("The exchange-rate service could not provide this data. Try another date or try again later.") from error
    except requests.RequestException as error:
        raise RuntimeError("The exchange-rate request failed. Please try again later.") from error

    try:
        return response.json()
    except ValueError as error:
        raise RuntimeError("The exchange-rate service returned an unreadable response. Please try again later.") from error
