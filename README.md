# Currency Converter — Stage 1

Backend foundation for UTS 94692 Data Science Practice Assignment 2.
Retrieves exchange rates from the open-source Frankfurter API and performs
currency conversion calculations. The Streamlit interface is not implemented.

## Architecture

- `api.py`: generic JSON GET requests using `requests`, with a 10-second
  timeout and clear `RuntimeError` exceptions for HTTP/network and JSON errors.
- `frankfurter.py`: currency list, latest rate and historical rate endpoints.
  Both rate functions return `date`, `base`, `target` and `rate` in a dictionary.
- `currency.py`: `convert_amount(amount, exchange_rate)` and
  `inverse_rate(exchange_rate)`, with finite-number and range validation.
- `app.py`: placeholder for the later Streamlit interface.

## Setup and backend example

Use Python 3.10 or later. Install the only external dependency:

```sh
python -m pip install requests
```

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
rounded, leaving display formatting to the later interface. Invalid inputs
raise `ValueError`; failed requests or invalid API responses raise `RuntimeError`.
Currency codes are normalized; unsupported codes are rejected by the API.
Select two different currencies. Historical dates must use `YYYY-MM-DD` and
must not be in the future. Dates without published data may return an earlier
working day's rate; always display the returned date. Unavailable historical
data produces an error rather than an invented rate.

The project uses the [Frankfurter v1 API](https://frankfurter.dev/v1/)
to match the assignment's currency, latest and historical endpoints.
Although superseded by v2, v1 remains available. No API key is required.
