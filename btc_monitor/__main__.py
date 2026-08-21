from __future__ import annotations

import json

from .app import run_monitor


def main() -> None:
    status = run_monitor()
    print(json.dumps(status, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
