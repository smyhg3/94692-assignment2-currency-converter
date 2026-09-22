"""Exercise the real UI and backend using simulated HTTP responses."""

from datetime import date, timedelta
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import requests
import streamlit as st
from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[1] / "app.py"


def response_for(url, params=None, timeout=None):
    """Provide predictable currencies and quotes at the HTTP boundary."""
    response = Mock()
    if url.endswith("/currencies"):
        response.json.return_value = {"AUD": "Australian Dollar", "USD": "US Dollar", "EUR": "Euro"}
    else:
        response.json.return_value = {
            "base": params["base"], "date": "2024-05-17",
            "rates": {params["symbols"]: 0.65 if params["base"] == "AUD" else 1.54},
        }
    return response


class AppTests(unittest.TestCase):
    def setUp(self):
        st.cache_data.clear()
        self.patcher = patch("api.requests.get", side_effect=response_for)
        self.get = self.patcher.start()
        self.addCleanup(self.patcher.stop)
        self.addCleanup(st.cache_data.clear)
        self.app = AppTest.from_file(str(APP_PATH), default_timeout=20).run()
        self.assertFalse(self.app.exception)

    def convert(self):
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        return "\n".join(item.value for item in self.app.markdown)

    def test_latest_and_large_amount_both_directions(self):
        self.assertEqual(len(self.app.selectbox[0].options), 3)
        self.app.number_input[0].set_value(1000.0).run()
        output = self.convert()
        self.assertIn("1,000.00 AUD = 650.00 USD", output)
        self.assertIn("1 USD = 1.53846 AUD", output)
        self.app.selectbox[0].set_value("USD").run()
        self.app.selectbox[1].set_value("AUD").run()
        self.assertIn("1,000.00 USD = 1,540.00 AUD", self.convert())

    def test_historical_actual_date(self):
        self.app.radio[0].set_value("Historical exchange rate").run()
        self.app.date_input[0].set_value(date(2024, 5, 19)).run()
        output = self.convert()
        self.assertIn("Exchange rate date: 2024-05-17", output)
        self.assertIn("2024-05-19", self.app.info[0].value)

    def test_zero_amount(self):
        self.app.number_input[0].set_value(0.0).run()
        self.assertIn("0.00 AUD = 0.00 USD", self.convert())

    def test_same_currency_skips_request(self):
        self.app.selectbox[1].set_value("AUD").run()
        count = self.get.call_count
        self.convert()
        self.assertIn("different currencies", self.app.error[0].value)
        self.assertEqual(self.get.call_count, count)

    def test_invalid_amounts_skip_request(self):
        # Simulate values bypassing the widget's minimum constraint.
        for amount in (-1.0, float("nan"), float("inf")):
            with self.subTest(amount=amount), patch("streamlit.number_input", return_value=amount):
                count = self.get.call_count
                self.convert()
                self.assertTrue(self.app.error)
                self.assertEqual(self.get.call_count, count)

    def test_missing_and_future_dates_skip_request(self):
        self.app.radio[0].set_value("Historical exchange rate").run()
        for value in (None, date.today() + timedelta(days=1)):
            with self.subTest(value=value), patch("streamlit.date_input", return_value=value):
                count = self.get.call_count
                self.convert()
                self.assertTrue(self.app.error)
                self.assertEqual(self.get.call_count, count)

    def test_network_errors_and_recovery(self):
        for failure, message in ((requests.Timeout, "timed out"),
                                 (requests.ConnectionError, "internet connection"),
                                 (requests.HTTPError, "could not provide")):
            self.get.side_effect = failure("private diagnostic detail")
            self.convert()
            self.assertIn(message, self.app.error[0].value)
            self.assertNotIn("private diagnostic detail", self.app.error[0].value)
        self.get.side_effect = response_for
        self.assertIn("Converted amount:", self.convert())
        self.assertFalse(self.app.error)

    def test_missing_rate_and_invalid_json(self):
        response = Mock()
        response.json.return_value = {"rates": {}}
        self.get.side_effect = None
        self.get.return_value = response
        self.convert()
        self.assertIn("missing or invalid", self.app.error[0].value)
        response.json.side_effect = ValueError("private parser details")
        self.convert()
        self.assertIn("unreadable response", self.app.error[0].value)

    def test_currency_failure_and_retry(self):
        st.cache_data.clear()
        self.get.side_effect = requests.ConnectionError("offline")
        self.app.run()
        self.assertFalse(self.app.exception)
        self.assertIn("Unable to load currencies", self.app.error[0].value)
        self.get.side_effect = response_for
        self.app.button[0].click().run()
        self.assertFalse(self.app.exception)
        self.assertFalse(self.app.error)
        self.assertEqual(len(self.app.selectbox), 2)


if __name__ == "__main__":
    unittest.main()
