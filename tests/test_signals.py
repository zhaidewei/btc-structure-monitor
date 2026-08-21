import datetime as dt
import unittest

from btc_monitor.market import PricePoint
from btc_monitor.signals import build_snapshot, signal_series


def points(values):
    start = dt.date(2020, 1, 1)
    return [PricePoint(start + dt.timedelta(days=index), value, value) for index, value in enumerate(values)]


class SignalTests(unittest.TestCase):
    def test_requires_complete_long_window(self):
        with self.assertRaises(ValueError):
            signal_series(points([100.0] * 299), 35, 300)

    def test_detects_golden_cross(self):
        values = [100.0] * 300 + [100.0 + index for index in range(1, 50)]
        rows = signal_series(points(values), 35, 300)
        self.assertTrue(any(row["crossover"] == "GOLDEN" for row in rows))
        self.assertEqual(rows[-1]["signal"], "BTC")

    def test_snapshot_counts_rapid_reversals(self):
        values = [100.0] * 300
        for block in range(8):
            values.extend(([150.0] if block % 2 == 0 else [50.0]) * 40)
        snapshot, _ = build_snapshot(points(values), 5, 300, 2.0)
        self.assertGreaterEqual(snapshot.crossover_count_12m, 2)
        self.assertGreaterEqual(snapshot.rapid_reversal_count_12m, 1)


if __name__ == "__main__":
    unittest.main()
