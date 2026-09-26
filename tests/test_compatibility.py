"""Regression coverage for the recovered assignment template interfaces."""

from datetime import date
import unittest
from unittest.mock import Mock, patch

from api import get_url
from currency import format_output, reverse_rate, round_rate
from frankfurter import (
    get_currencies_list, get_historical_rate, get_latest_rates, get_rate_trend,
)


class TemplateCompatibilityTests(unittest.TestCase):
    def test_get_url_returns_response_status_and_text(self):
        for status, text in ((200, '{"AUD": "Australian Dollar"}'), (404, "Not found")):
            with self.subTest(status=status), patch(
                "api.requests.get", return_value=Mock(status_code=status, text=text)
            ):
                self.assertEqual(get_url("https://example.test"), (status, text))

    def test_round_rate(self):
        self.assertEqual(round_rate(1.234567), 1.2346)
        self.assertEqual(round_rate(-1.234567), -1.2346)

    def test_reverse_rate(self):
        self.assertEqual(reverse_rate(0), 0)
        self.assertEqual(reverse_rate(3), 0.3333)
        self.assertEqual(reverse_rate(-3), -0.3333)

    def test_format_output(self):
        self.assertEqual(
            format_output("2024-05-15", "AUD", "USD", 0.66421, 1000),
            "The conversion rate on 2024-05-15 from AUD to USD was 0.66421. "
            "So 1,000.00 in AUD correspond to 664.21 in USD. The inverse rate was 1.50555.",
        )

    def test_currencies_list(self):
        with patch("frankfurter.get_json", return_value={"AUD": "Australian Dollar", "USD": "US Dollar"}):
            self.assertCountEqual(get_currencies_list(), ["AUD", "USD"])

    def test_currencies_failure(self):
        with patch("frankfurter.get_json", side_effect=RuntimeError("Unavailable")):
            self.assertIsNone(get_currencies_list())

    def test_latest_rates(self):
        quote = {"date": "2024-05-15", "base": "AUD", "rates": {"USD": 0.66421}}
        with patch("frankfurter.get_json", return_value=quote):
            for amount in (0, 1000):
                self.assertEqual(get_latest_rates("AUD", "USD", amount), ("2024-05-15", 0.66421))

    def test_latest_failure(self):
        with patch("frankfurter.get_json", side_effect=RuntimeError("Unavailable")):
            self.assertEqual(get_latest_rates("AUD", "USD", 100), (None, None))

    def test_historical_interfaces(self):
        quote = {"date": "2024-05-17", "base": "AUD", "rates": {"USD": 0.65}}
        with patch("frankfurter.get_json", return_value=quote):
            expected = {"date": "2024-05-17", "base": "AUD", "target": "USD", "rate": 0.65}
            self.assertEqual(get_historical_rate("AUD", "USD", "2024-05-18"), expected)
            self.assertEqual(get_historical_rate("AUD", "USD", historical_date="2024-05-18"), expected)
            for amount in (0, 1000):
                self.assertEqual(get_historical_rate("AUD", "USD", "2024-05-18", amount), 0.65)
                self.assertEqual(get_historical_rate("AUD", "USD", from_date="2024-05-18", amount=amount), 0.65)

    def test_historical_failure_preserves_current_exception(self):
        with patch("frankfurter.get_json", side_effect=RuntimeError("Unavailable")):
            self.assertIsNone(get_historical_rate("AUD", "USD", "2024-05-15", 100))
            with self.assertRaises(RuntimeError):
                get_historical_rate("AUD", "USD", "2024-05-15")

    def test_quarterly_trend(self):
        rates = {
            "2023-12-29": {"USD": 0.60},
            "2024-01-02": {"USD": 0.61},
            "2024-03-28": {"USD": 0.62},
            "2024-04-02": {"USD": 0.63},
            "2024-06-28": {"USD": 0.64},
        }
        with patch("frankfurter.date", wraps=date) as calendar, patch(
            "frankfurter.get_json", return_value={"base": "AUD", "rates": rates}
        ) as request:
            calendar.today.return_value = date(2024, 6, 30)
            result = get_rate_trend("AUD", "USD", 2)
            request.assert_called_once_with(
                "https://api.frankfurter.dev/v1/2022-06-30..2024-06-30",
                params={"base": "AUD", "symbols": "USD"},
            )
        self.assertIsInstance(result, dict)
        quarters = set()
        for date_text, rate in result.items():
            self.assertEqual(rate, rates[date_text]["USD"])
            published_date = date.fromisoformat(date_text)
            quarters.add((published_date.year, (published_date.month - 1) // 3))
        self.assertEqual(len(result), 3)
        self.assertEqual(len(quarters), len(result))
