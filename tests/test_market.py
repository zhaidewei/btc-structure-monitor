import datetime as dt
import json
import unittest
from unittest.mock import patch

from btc_monitor.market import fetch_coinbase_candles


class CoinbaseMarketTests(unittest.TestCase):
    @patch("btc_monitor.market._request")
    def test_parses_sorts_and_filters_daily_candles(self, request):
        request.return_value = json.dumps(
            [
                [1767312000, 90, 120, 101, 110, 1],
                [1767225600, 80, 110, 100, 105, 1],
                [1767139200, 70, 100, 95, 99, 1],
            ]
        ).encode()

        points = fetch_coinbase_candles(
            "BTC-EUR", dt.date(2026, 1, 1), dt.date(2026, 1, 2)
        )

        self.assertEqual([point.date for point in points], [dt.date(2026, 1, 1), dt.date(2026, 1, 2)])
        self.assertEqual(points[0].open_eur, 100.0)
        self.assertEqual(points[-1].close_eur, 110.0)


if __name__ == "__main__":
    unittest.main()
