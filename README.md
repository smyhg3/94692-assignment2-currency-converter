# Currency Converter

**Student Name:** Hongyi Guo  
**Student ID:** 26295358  
**Course:** 94692

**Table of Contents**

1. [Overview](#overview)
2. [Setup and Usage](#setup-and-usage)
3. [Architecture](#architecture)
4. [Function Reference](#function-reference)
5. [Key Workflows](#key-workflows)
6. [Tests](#tests)
7. [Development and Version Control](#development-and-version-control)
8. [API Reference](#api-reference)

## Overview

A Python Streamlit application that uses the Frankfurter API for latest and
historical currency conversion. It displays converted amounts, inverse rates
and a fixed three-year exchange-rate trend below the latest result.

## Setup and Usage

Use Python 3.10 or later. Install the dependencies:

```sh
python -m pip install requests streamlit
```

From the project directory, start the application:

```sh
python -m streamlit run app.py
```

Choose two different currencies and enter a non-negative amount. Click
**Get latest conversion rate**, or select a historical date and click
**Get historical conversion rate**. Zero is allowed; future dates are rejected.
An internet connection is required.

Each section has a separate read-only result box. Results retain the inputs
used until that section is requested again; a failed conversion clears only
its own result. Amounts display two decimal places and rates six significant
digits. Calculations use the unrounded values.

After a successful latest conversion, **Rate Trend Over the Last 3 years**
appears below its result box, with Date on the x-axis and Rate on the y-axis.
Changing currencies hides the old chart until the latest button is clicked
again. Unavailable trend data produces a warning without removing the
conversion result. The historical section has no chart.

## Architecture

- `app.py`: Streamlit inputs, interaction, backend orchestration, result display and chart rendering.
- `api.py`: generic HTTP GET requests and request/JSON error handling.
- `frankfurter.py`: Frankfurter endpoints, response parsing and data validation.
- `currency.py`: amount validation, currency calculations and final result formatting.
- `README.md`: project documentation, usage instructions and implementation reference.

## Function Reference

The table lists all 16 named functions, including private helpers. `None` means
no value is returned on successful completion. Invalid inputs raise
`ValueError`; request failures or invalid API responses raise `RuntimeError`.

| Module | Function | Parameters | Returns | Purpose |
|---|---|---|---|---|
| `app.py` | `load_currencies` | None | Currency code/name dictionary | Load and cache supported currencies for one hour. |
| `app.py` | `main` | None | `None` | Render shared inputs, both conversion sections and the footer. |
| `app.py` | `show_conversion_section` | `section, source, target, amount` | `None` | Handle one conversion section, preserve its result and display the latest-rate chart when applicable. |
| `api.py` | `get_json` | `url, params=None` | Decoded JSON | Perform an HTTP GET with a ten-second timeout and translate request/JSON errors. |
| `frankfurter.py` | `_currency_code` | `code` | `str` | Validate and normalise a three-letter currency code. |
| `frankfurter.py` | `get_currencies` | None | Currency code/name dictionary | Retrieve and validate the supported currency list. |
| `frankfurter.py` | `_get_rate` | `endpoint, from_currency, to_currency` | Dictionary: `date, base, target, rate` | Retrieve and validate a single exchange-rate quote. |
| `frankfurter.py` | `get_latest_rate` | `from_currency, to_currency` | Quote dictionary | Retrieve the latest available quote. |
| `frankfurter.py` | `get_historical_rate` | `from_currency, to_currency, historical_date` | Quote dictionary | Validate a `YYYY-MM-DD` date and retrieve its available quote. |
| `frankfurter.py` | `get_three_year_rates` | `from_currency, to_currency` | Sorted list of `Date`/`Rate` dictionaries | Retrieve and validate rates within the last three calendar years; `Date` values are Python dates. |
| `currency.py` | `_validate_number` | `value, name` | `None` | Reject non-numeric, boolean and non-finite values. |
| `currency.py` | `_validate_rate` | `exchange_rate` | `None` | Require a positive, finite numeric rate. |
| `currency.py` | `validate_amount` | `amount` | `None` | Require a non-negative, finite numeric amount. |
| `currency.py` | `convert_amount` | `amount, exchange_rate` | Numeric converted amount | Multiply the amount by the rate and validate the result. |
| `currency.py` | `inverse_rate` | `exchange_rate` | `float` | Calculate and validate the reciprocal rate. |
| `currency.py` | `format_conversion_result` | `rate_date, from_currency, to_currency, rate, amount, converted_amount, inverse_rate` | `str` | Format supplied values using the required wording without recalculation. |

Three anonymous lambdas support these functions: two in `app.py` format
currency option labels, and one in `frankfurter.py` selects the date as the
sorting key. They are callbacks rather than primary API functions.

## Key Workflows

### Historical Date Handling

Historical date fallback is determined by the data returned by the Frankfurter
API. The application does not manually search backwards through dates.

```text
WHEN the historical conversion button is clicked:
    Clear only the historical result
    Validate different currencies, a selected non-future date, and amount
    Convert the selected date to YYYY-MM-DD

    Backend validates the date string and normalises the currency codes
    Request the historical endpoint
    Validate the returned base currency, target rate and publication date
    Require a positive finite rate and a date no later than the request

    Calculate converted amount and inverse rate
    Format and save the historical result with both dates

ON input or request failure:
    Display an error; keep the latest result unchanged

WHEN displaying a saved historical result:
    Display its actual exchange-rate date
    If the returned date differs from the requested date:
        Display a fallback notice
    Display the read-only result text
```

### Three-Year Rate Trend

The range uses calendar years rather than a fixed number of days. Only returned
published rates within the range are plotted; missing days are not filled in.

```text
AFTER a successful latest conversion has been saved:
    Normalise currency codes and require different currencies
    Set end date to today
    Set start date to the same month/day three calendar years earlier
    If that date is invalid because of February 29:
        Use February 28 of that year

    Request the date-range endpoint for the selected currency pair
    Validate the response base currency and rates dictionary
    For each returned record:
        Validate its date and positive finite target rate
        Reject dates later than today
        Keep the record only if its date is on or after the start date
    Reject an empty result
    Sort records by date and store them with the latest result

IF trend retrieval or validation fails:
    Store an empty trend; preserve the successful conversion

WHEN displaying a saved latest result:
    Show the trend heading below the result box
    If selected currencies differ from the stored pair:
        Ask the user to request the latest conversion again
    Otherwise, if no trend data is available:
        Show a warning
    Otherwise:
        Draw Date against Rate
```

## Tests

After installing dependencies, run the offline regression tests from the
project directory:

```sh
python -m unittest discover -s tests -v
```

The tests use simulated HTTP responses and Streamlit's AppTest to cover input
validation, calculations, result formatting, independent result boxes,
historical date handling, trend data and chart placement, and API/network
errors. They require no internet access and do not verify live API availability.

The `tests/` directory is retained in the GitHub repository for development
and regression testing, but is not included in the Canvas submission ZIP.

## Development and Version Control

The project was developed incrementally using Git and GitHub. Commits record
backend development, Streamlit integration, validation and testing, the
three-year trend chart, and documentation refinements.

## API Reference

The application uses the [Frankfurter v1 API](https://frankfurter.dev/v1/)
for currencies, latest rates, historical rates and date-range time series.
No API key is required. HTTP requests use a ten-second timeout; connection,
timeout, HTTP and unreadable JSON failures produce user-facing error messages.
