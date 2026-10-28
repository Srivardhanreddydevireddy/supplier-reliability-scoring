
import csv
import sqlite3
from pathlib import Path

DB_PATH = "supplier_reliability.db"
DATA_DIR = Path("output")

load_order = [
    "Supplier.csv",
    "Site.csv",
    "Contract.csv",
    "PurchaseOrder.csv",
    "POLine.csv",
    "Shipment.csv",
    "DeliveryEvent.csv",
    "Inspection.csv",
    "Invoice.csv",
    "RiskSignal.csv",
    "SupplierScore.csv",
]

connection = sqlite3.connect(DB_PATH)

try:
    connection.execute("PRAGMA foreign_keys = ON")

    connection.executescript("""
        DROP TABLE IF EXISTS SupplierScore;
        DROP TABLE IF EXISTS RiskSignal;
        DROP TABLE IF EXISTS Invoice;
        DROP TABLE IF EXISTS Inspection;
        DROP TABLE IF EXISTS DeliveryEvent;
        DROP TABLE IF EXISTS Shipment;
        DROP TABLE IF EXISTS POLine;
        DROP TABLE IF EXISTS PurchaseOrder;
        DROP TABLE IF EXISTS Contract;
        DROP TABLE IF EXISTS Site;
        DROP TABLE IF EXISTS Supplier;
    """)

    connection.executescript(
        Path("schema.sql").read_text(encoding="utf-8")
    )

    for filename in load_order:
        csv_path = DATA_DIR / filename

        with csv_path.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            columns = reader.fieldnames

            if not columns:
                raise ValueError(f"Missing CSV headers: {filename}")

            column_sql = ", ".join(f'"{c}"' for c in columns)
            placeholders = ", ".join("?" for _ in columns)

            sql = (
                f'INSERT INTO "{csv_path.stem}" ({column_sql}) '
                f"VALUES ({placeholders})"
            )

            rows = [tuple(row[c] for c in columns) for row in reader]
            connection.executemany(sql, rows)

            print(f"Loaded {filename}: {len(rows)} records")

    connection.commit()
    print("\nDatabase created successfully!")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()