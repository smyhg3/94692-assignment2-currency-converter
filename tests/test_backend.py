"""Offline regression tests for HTTP, API validation and calculations."""

from datetime import date, timedelta
import unittest
from unittest.mock import patch

import requests

from api import get_json
from currency import convert_amount, format_conversion_result, inverse_rate, validate_amount
from frankfurter import get_currencies, get_historical_rate, get_latest_rate, get_three_year_rates


class CalculationTests(unittest.TestCase):
    def test_format_conversion_result_uses_supplied_values(self):
        # Deliberately distinct supplied results catch accidental recalculation.
        result = format_conversion_result(
            "2024-05-15", "AUD", "USD", 0.66421, 1000, 1234.567, 1.23456789
        )
        self.assertEqual(
            result,
            "The conversion rate on 2024-05-15 from AUD to USD was 0.66421. "
            "So 1,000.00 in AUD correspond to 1,234.57 in USD. The inverse rate was 1.23457.",
        )

    def test_conversion_and_inverse(self):
        for amount in (0, 100, 1000):
            self.assertAlmostEqual(convert_amount(amount, 0.65), amount * 0.65)
        self.assertAlmostEqual(inverse_rate(0.65), 1 / 0.65)

    def test_invalid_amounts(self):
        for amount in (-1, None, "100", True, float("nan"), float("inf"), 10 ** 400):
            with self.subTest(amount=repr(amount)), self.assertRaises(ValueError):
                validate_amount(amount)

    def test_invalid_rates(self):
        for rate in (0, -1, None, "0.65", True, float("nan"), float("inf")):
            for operation in (inverse_rate, lambda value: convert_amount(100, value)):
                with self.subTest(rate=rate), self.assertRaises(ValueError):
                    operation(rate)

    def test_nonfinite_results(self):
        with self.assertRaises(ValueError):
            convert_amount(1e308, 2)
        with self.assertRaises(ValueError):
            inverse_rate(5e-324)


class HttpTests(unittest.TestCase):
    @patch("api.requests.get")
    def test_success_and_timeout_setting(self, get):
        get.return_value.json.return_value = {"ok": True}
        self.assertEqual(get_json("https://example.test", {"a": 1}), {"ok": True})
        get.assert_called_once_with("https://example.test", params={"a": 1}, timeout=10)
        get.return_value.raise_for_status.assert_called_once()

    @patch("api.requests.get")
    def test_network_failures_do_not_leak_details(self, get):
        for failure, message in ((requests.Timeout, "timed out"),
                                 (requests.ConnectionError, "internet connection"),
                                 (requests.RequestException, "request failed")):
            get.side_effect = failure("private diagnostic detail")
            with self.subTest(failure=failure), self.assertRaises(RuntimeError) as caught:
                get_json("https://example.test")
            self.assertIn(message, str(caught.exception))
            self.assertNotIn("private diagnostic detail", str(caught.exception))

    @patch("api.requests.get")
    def test_http_errors(self, get):
        for status in (400, 404, 429, 500):
            get.return_value.raise_for_status.side_effect = requests.HTTPError(str(status))
            with self.subTest(status=status), self.assertRaisesRegex(RuntimeError, "could not provide"):
                get_json("https://example.test")

    @patch("api.requests.get")
    def test_unreadable_json(self, get):
        get.return_value.json.side_effect = ValueError("Invalid JSON")
        with self.assertRaisesRegex(RuntimeError, "unreadable response"):
            get_json("https://example.test")


class FrankfurterTests(unittest.TestCase):
    @patch("frankfurter.get_json")
    def test_three_year_series_range_sorting_and_leap_day(self, get):
        with patch("frankfurter.date", wraps=date) as clock:
            clock.today.return_value = date(2024, 2, 29)
            get.return_value = {
                "base": "AUD", "rates": {
                    "2024-02-29": {"USD": 0.66}, "2021-02-26": {"USD": 0.64},
                    "2021-03-01": {"USD": 0.65},
                },
            }
            rows = get_three_year_rates("aud", "usd")
        self.assertTrue(get.call_args.args[0].endswith("2021-02-28..2024-02-29"))
        self.assertEqual(get.call_args.kwargs["params"], {"base": "AUD", "symbols": "USD"})
        self.assertEqual(rows, [{"Date": date(2021, 3, 1), "Rate": 0.65},
                                {"Date": date(2024, 2, 29), "Rate": 0.66}])

    @patch("frankfurter.get_json")
    def test_three_year_series_invalid_data(self, get):
        today = date.today().isoformat()
        payloads = [None, {}, {"base": "AUD", "rates": {}},
                    {"base": "EUR", "rates": {today: {"USD": 0.65}}},
                    {"base": "AUD", "rates": {"bad-date": {"USD": 0.65}}},
                    {"base": "AUD", "rates": {today: {}}}]
        payloads += [{"base": "AUD", "rates": {today: {"USD": rate}}}
                     for rate in (0, -1, True, None, "0.65", float("nan"), float("inf"))]
        for payload in payloads:
            get.return_value = payload
            with self.subTest(payload=payload), self.assertRaises(RuntimeError):
                get_three_year_rates("AUD", "USD")
        get.reset_mock()
        with self.assertRaises(ValueError):
            get_three_year_rates("AUD", "AUD")
        get.assert_not_called()

    @patch("frankfurter.get_json")
    def test_currency_list(self, get):
        get.return_value = {"AUD": "Australian Dollar", "USD": "US Dollar"}
        self.assertEqual(len(get_currencies()), 2)
        for payload in (None, [], {}, {"AUD": None}, {"AUD": " "}, {"bad": "Name"}):
            get.return_value = payload
            with self.subTest(payload=payload), self.assertRaises(RuntimeError):
                get_currencies()

    @patch("frankfurter.get_json")
    def test_latest_both_directions(self, get):
        for source, target, rate in (("AUD", "USD", 0.65), ("USD", "AUD", 1.54)):
            get.return_value = {"base": source, "date": "2024-05-15", "rates": {target: rate}}
            quote = get_latest_rate(source, target)
            self.assertEqual(quote["rate"], rate)
            self.assertEqual(get.call_args.kwargs["params"], {"base": source, "symbols": target})

    @patch("frankfurter.get_json")
    def test_historical_fallback(self, get):
        get.return_value = {"base": "AUD", "date": "2024-05-17", "rates": {"USD": 0.65}}
        quote = get_historical_rate("AUD", "USD", "2024-05-19")
        self.assertEqual(quote["date"], "2024-05-17")
        self.assertTrue(get.call_args.args[0].endswith("2024-05-19"))

    @patch("frankfurter.get_json")
    def test_invalid_inputs_skip_http(self, get):
        with self.assertRaises(ValueError):
            get_latest_rate("AUD", "aud")
        for value in (None, "2024-02-30", "20240515", (date.today() + timedelta(days=1)).isoformat()):
            with self.subTest(value=value), self.assertRaises(ValueError):
                get_historical_rate("AUD", "USD", value)
        get.assert_not_called()

    @patch("frankfurter.get_json")
    def test_malformed_rates(self, get):
        valid = {"base": "AUD", "date": "2024-05-15", "rates": {"USD": 0.65}}
        payloads = [None, [], {}, {**valid, "rates": {}}, {**valid, "base": "EUR"},
                    {**valid, "date": "bad"}, {**valid, "date": "20240515"},
                    {**valid, "date": (date.today() + timedelta(days=1)).isoformat()}]
        payloads += [{**valid, "rates": {"USD": rate}} for rate in
                     (0, -1, None, "0.65", True, float("nan"), float("inf"), 10 ** 400)]
        for payload in payloads:
            get.return_value = payload
            with self.subTest(payload=payload), self.assertRaises(RuntimeError):
                get_latest_rate("AUD", "USD")
        get.return_value = valid
        with self.assertRaises(RuntimeError):
            get_historical_rate("AUD", "USD", "2024-05-14")


if __name__ == "__main__":
    unittest.main()
