"""List the included manuscript table summaries and their CSV columns."""

from __future__ import annotations

import csv
from pathlib import Path


def main() -> None:
    folder = Path(__file__).resolve().parents[1] / "results" / "reported"
    for path in sorted(folder.glob("*.csv")):
        with path.open(newline="", encoding="utf-8-sig") as stream:
            rows = list(csv.DictReader(stream))
        if not rows:
            raise ValueError(f"Empty reported table: {path.name}")
        print(f"{path.name}: {len(rows)} rows; columns={', '.join(rows[0])}")


if __name__ == "__main__":
    main()
