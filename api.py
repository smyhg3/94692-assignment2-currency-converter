"""Generic HTTP helpers for JSON APIs."""

import requests


def get_json(url, params=None):
    """Return decoded JSON or raise RuntimeError for request/JSON failures."""
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as error:
        raise RuntimeError(f"HTTP request failed: {error}") from error

    try:
        return response.json()
    except ValueError as error:
        raise RuntimeError("The server returned invalid JSON.") from error
