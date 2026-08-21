import tempfile
import unittest
from pathlib import Path

from btc_monitor.io import read_json, write_json


class IoTests(unittest.TestCase):
    def test_atomic_json_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            write_json(path, {"signal": "CASH"})
            self.assertEqual(read_json(path), {"signal": "CASH"})


if __name__ == "__main__":
    unittest.main()
