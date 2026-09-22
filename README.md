# Currency Converter — Stage 2

Streamlit web app for UTS 94692 Data Science Practice Assignment 2.
Retrieves exchange rates from the open-source Frankfurter API and performs
currency conversion calculations, with latest and historical rate options.

## Architecture

- `api.py`: generic JSON GET requests using `requests`, with a 10-second
  timeout and clear `RuntimeError` exceptions for HTTP/network and JSON errors.
- `frankfurter.py`: currency list, latest rate and historical rate endpoints.
  Both rate functions return `date`, `base`, `target` and `rate` in a dictionary.
- `currency.py`: `convert_amount(amount, exchange_rate)` and
  `inverse_rate(exchange_rate)`, with finite-number and range validation.
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

Choose source and target currencies, enter a non-negative amount, select latest
or historical exchange rate, and click **Convert**. Historical mode displays a
date input. Currency choices come from Frankfurter and are cached for one hour.
Results show the actual rate date, exchange rate, converted amount and inverse
rate. Amounts display two decimal places; rates display six significant digits.
Identical currencies, invalid inputs, unavailable data and API/network failures
produce error messages. An internet connection is required.

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

Amounts must be non-negative; rates must be positive. Calculations are not
rounded, leaving display formatting to the Streamlit interface. Invalid inputs
raise `ValueError`; failed requests or invalid API responses raise `RuntimeError`.
Currency codes are normalized; unsupported codes are rejected by the API.
Select two different currencies. Historical dates must use `YYYY-MM-DD` and
must not be in the future. Dates without published data may return an earlier
working day's rate; always display the returned date. Unavailable historical
data produces an error rather than an invented rate.

The project uses the [Frankfurter v1 API](https://frankfurter.dev/v1/)
to match the assignment's currency, latest and historical endpoints.
Although superseded by v2, v1 remains available. No API key is required.
