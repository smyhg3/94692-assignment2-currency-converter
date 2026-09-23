# Currency Converter — Stage 4

**Student Name:** Hongyi Guo  
**Student ID:** 26295358  
**Course:** UTS 94692 Data Science Practice  
**Assignment:** Assignment 2

Streamlit web app for UTS 94692 Data Science Practice Assignment 2.

Retrieves exchange rates from the open-source Frankfurter API and performs
currency conversion calculations, with latest and historical rate options.

## Development Iterations

This project was developed incrementally across four stages, with each stage focusing on a specific part of the assignment.

### Stage 1 — Backend foundation

The first stage focused on separating the core backend responsibilities before building the user interface.

- Added generic HTTP request handling in `api.py`.
- Implemented Frankfurter API integration in `frankfurter.py`.
- Added currency conversion and inverse-rate calculations in `currency.py`.
- Established the initial project structure and Git/GitHub workflow.

### Stage 2 — Streamlit interface and core conversion workflow

The second stage connected the backend to a working Streamlit application.

- Added amount, source currency and target currency inputs.
- Implemented latest exchange-rate conversion.
- Implemented historical exchange-rate lookup by date.
- Added separate read-only result boxes for latest and historical conversions.
- Matched the required assignment result wording through `format_conversion_result(...)`.

### Stage 3 — Validation, reliability and testing

The third stage focused on making the application more robust rather than adding major new features.

- Added input validation for amounts, currency selections and dates.
- Improved API/network error handling and user-facing messages.
- Added protection against invalid, missing or non-finite rate data.
- Added offline regression tests for backend logic and Streamlit behaviour.
- Verified historical-date fallback behaviour and independent latest/historical results.

### Stage 4 — Assignment alignment, visualisation and final refinement

The final stage focused on aligning the implementation more closely with the assignment example and improving code quality.

- Reorganised responsibilities so result formatting is handled by `currency.py`.
- Added the required three-year exchange-rate trend chart below the latest conversion result.
- Refined the Streamlit layout while keeping the assignment structure clear.
- Simplified code and improved comments/docstrings without changing observable behaviour.
- Cleaned submission files, updated documentation and prepared the final release.

This staged workflow was tracked through Git commits on the `development` branch and then integrated into `main` through pull requests.

## Architecture

- `api.py`: generic JSON GET requests using `requests`, with a 10-second
  timeout and clear `RuntimeError` exceptions for HTTP/network and JSON errors.

- `frankfurter.py`: currency list, latest rate and historical rate endpoints.
  Both rate functions return `date`, `base`, `target` and `rate` in a dictionary.
  `get_three_year_rates(from_currency, to_currency)` retrieves and validates
  time-series rates from three calendar years ago through today, returning
  sorted `Date`/`Rate` records. February 29 maps to February 28 when necessary.

- `currency.py`: currency calculations and final result text formatting.
  `convert_amount(amount, exchange_rate)` and
  `inverse_rate(exchange_rate)`, with finite-number and range validation.
  `validate_amount(amount)` also checks inputs before the UI requests a rate.
  `format_conversion_result(rate_date, from_currency, to_currency, rate, amount,
  converted_amount, inverse_rate)` returns the assignment's English result text
  using the supplied values, without recalculating or making API requests.

- `app.py`: Streamlit inputs, API currency-list caching, conversion results
  and user-facing error messages. Backend modules remain independent of Streamlit.

## Setup and run

Use Python 3.10 or later. Install the external dependencies:

```sh
python -m pip install requests streamlit
```

From this directory, start the web app:

```sh
python -m streamlit run app.py
```

Choose source and target currencies and enter a non-negative amount.

Click **Get latest conversion rate** for the latest quote, or select a historical
date and click **Get historical conversion rate**.

Each section has its own read-only result box. Results remain visible until that
section is requested again; their text records the inputs used. A failed request
clears only its own result.

After a successful latest conversion, **Rate Trend Over the Last 3 years**
appears directly below its result box. The line chart plots Date against Rate
for the selected currency pair, using published rates within the last three
calendar years; non-working days are not fabricated. The range is fixed.
Changing currencies hides the old chart until you click the latest button again.
Unavailable trend data shows a warning without removing the conversion result.
The historical section does not display a trend chart.

Currency choices come from Frankfurter and are cached for one hour.

Results show the actual rate date, exchange rate, converted amount and inverse
rate. Amounts display two decimal places; rates display six significant digits.

Identical currencies, invalid inputs, unavailable data and API/network failures
produce error messages. An internet connection is required.

Zero is allowed and converts to zero. Negative or non-finite amounts are rejected.

Connection failures, timeouts, HTTP errors and unreadable responses have separate
messages. Historical results may use an earlier working day, but a returned date
later than the requested date is rejected.

## Tests

Run the offline regression tests from this directory after installing dependencies:

```sh
python -m unittest discover -s tests -v
```

These tests use simulated HTTP responses and Streamlit's AppTest to cover input
validation, calculations, historical date fallback, response validation and
network errors. They do not require internet access or verify live API availability.

The `tests/` directory is maintained in the GitHub repository for development
and regression testing, but is not required in the final Canvas submission ZIP.

## Backend example

From this directory, run `python` and enter:

```python
from frankfurter import get_currencies, get_latest_rate, get_historical_rate
from currency import convert_amount, inverse_rate

currencies = get_currencies()

quote = get_latest_rate("AUD", "USD")

print(quote)
print(convert_amount(100, quote["rate"]))
print(inverse_rate(quote["rate"]))

print(get_historical_rate("AUD", "USD", "2024-05-15"))
```

Amounts must be non-negative; rates must be positive.

Calculations are not rounded; `format_conversion_result(...)` formats the final
text for display in Streamlit's read-only text area.

Invalid inputs raise `ValueError`; failed requests or invalid API responses raise
`RuntimeError`.

Currency codes are normalized; unsupported codes are rejected by the API.

Select two different currencies. Historical dates must use `YYYY-MM-DD` and must
not be in the future.

Dates without published data may return an earlier working day's rate; always
display the returned date. Unavailable historical data produces an error rather
than an invented rate.

## Version Control

This project was developed using Git and GitHub for version control.

Development was carried out incrementally on the `development` branch, with
separate commits used to record the main stages of implementation. Stable
changes were integrated into `main` through pull requests, allowing the project
history to show the progression from backend development to UI integration,
testing, visualisation and final refinement.

## API

The project uses the [Frankfurter v1 API](https://frankfurter.dev/v1/) to match
the assignment's currency, latest and historical endpoints.

Although superseded by v2, v1 remains available. No API key is required.
