import datetime as dt
import unittest

from btc_monitor.app import build_chart_history


class ChartHistoryTests(unittest.TestCase):
    def test_filters_chart_rows_from_configured_start(self):
        rows = [
            {
                "date": dt.date(2018, 12, 31),
                "price": 100.0,
                "short_sma": 90.0,
                "long_sma": 80.0,
                "signal": "BTC",
                "crossover": None,
            },
            {
                "date": dt.date(2019, 1, 1),
                "price": 101.0,
                "short_sma": 91.0,
                "long_sma": 81.0,
                "signal": "BTC",
                "crossover": None,
            },
        ]

        result = build_chart_history(rows, dt.date(2019, 1, 1))

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["date"], "2019-01-01")


if __name__ == "__main__":
    unittest.main()
