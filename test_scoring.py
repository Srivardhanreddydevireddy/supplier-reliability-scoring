
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from scoring import WEIGHTS, calculate_scores, clamp


DB_PATH = Path(__file__).resolve().parent / "supplier_reliability.db"
VALID_BANDS = {"EXCELLENT", "GOOD", "AVERAGE", "POOR"}


@pytest.fixture
def db():
    """Open the project database and close it after the test."""
    if not DB_PATH.exists():
        pytest.fail(f"Database not found: {DB_PATH}")

    connection = sqlite3.connect(DB_PATH)
    try:
        yield connection
    finally:
        connection.close()


def query(connection, sql):
    return pd.read_sql_query(sql, connection)


def test_database_exists():
    assert DB_PATH.is_file()


def test_supplier_count(db):
    result = query(db, "SELECT COUNT(*) AS total FROM Supplier")
    assert result.loc[0, "total"] == 1000


def test_supplier_scores_exist(db):
    result = query(db, "SELECT COUNT(*) AS total FROM SupplierScore")
    assert result.loc[0, "total"] == 1000


def test_every_supplier_has_exactly_one_score(db):
    result = query(
        db,
        """
        SELECT s.supplier_id, COUNT(sc.supplier_id) AS score_count
        FROM Supplier s
        LEFT JOIN SupplierScore sc
            ON s.supplier_id = sc.supplier_id
        GROUP BY s.supplier_id
        """
    )

    assert len(result) == 1000
    assert result["score_count"].eq(1).all()


def test_scores_are_valid(db):
    scores = query(
        db,
        """
        SELECT delivery_score, quality_score, cost_score,
               capacity_score, compliance_score, disruption_score,
               final_score
        FROM SupplierScore
        """
    )

    assert not scores.isna().any().any()
    assert scores.ge(0).all().all()
    assert scores.le(100).all().all()


def test_reliability_bands_are_valid(db):
    bands = query(
        db, "SELECT DISTINCT reliability_band FROM SupplierScore"
    )["reliability_band"]

    assert len(bands) > 0
    assert set(bands).issubset(VALID_BANDS)


def test_database_integrity(db):
    result = db.execute("PRAGMA integrity_check").fetchone()
    assert result[0] == "ok"


def test_no_foreign_key_violations(db):
    violations = db.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == []


def test_clamp_limits_values():
    assert clamp(-10) == 0.0
    assert clamp(0) == 0.0
    assert clamp(50) == 50
    assert clamp(100) == 100
    assert clamp(120) == 100.0


def test_weights_sum_to_one():
    assert sum(WEIGHTS.values()) == pytest.approx(1.0)


def test_calculate_scores_with_no_transaction_data():
    connection = sqlite3.connect(":memory:")

    try:
        connection.executescript("""
            CREATE TABLE Supplier (
                supplier_id TEXT,
                compliance_status TEXT,
                active INTEGER
            );

            CREATE TABLE Shipment (
                shipment_id TEXT,
                supplier_id TEXT,
                po_id TEXT,
                delivered_date TEXT,
                site_id TEXT,
                shipped_qty REAL
            );

            CREATE TABLE PurchaseOrder (
                po_id TEXT,
                supplier_id TEXT,
                required_date TEXT,
                po_total REAL
            );

            CREATE TABLE Inspection (
                shipment_id TEXT,
                accepted_qty REAL,
                inspected_qty REAL
            );

            CREATE TABLE Invoice (
                po_id TEXT,
                variance_amount REAL
            );

            CREATE TABLE Site (
                site_id TEXT,
                capacity_units REAL
            );

            CREATE TABLE RiskSignal (
                supplier_id TEXT,
                severity REAL,
                signal_type TEXT
            );

            INSERT INTO Supplier
            VALUES ('TEST-001', 'COMPLIANT', 1);
        """)

        results = calculate_scores(connection)

    finally:
        connection.close()

    assert len(results) == 1

    row = results[0]

    assert row[0] == "TEST-001"

    assert row[2:6] == (50.0, 50.0, 50.0, 50.0)

    assert row[6] == 100.0
    assert row[7] == 100.0

    assert row[8] == pytest.approx(62.5)
    assert row[9] == "AVERAGE"