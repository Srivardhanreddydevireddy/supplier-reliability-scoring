
import csv
from pathlib import Path

for path in sorted(Path("output").glob("*.csv")):
    with path.open("r", encoding="utf-8", newline="") as file:
        count = sum(1 for row in csv.DictReader(file))

    print(f"{path.name}: {count} records")