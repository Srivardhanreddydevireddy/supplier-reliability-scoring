
import sqlite3
from datetime import date

DB_PATH = "supplier_reliability.db"

WEIGHTS = {
    "delivery": 0.25,
    "quality": 0.25,
    "cost": 0.15,
    "capacity": 0.10,
    "compliance": 0.15,
    "disruption": 0.10,
}


def clamp(value):
    return max(0.0, min(100.0, value))


def calculate_scores(connection):
    suppliers = connection.execute(
        "SELECT supplier_id, compliance_status, active FROM Supplier"
    ).fetchall()

    results = []

    for supplier_id, compliance_status, active in suppliers:
        
        delivery = connection.execute("""
            SELECT COUNT(*),
                   SUM(CASE
                       WHEN sh.delivered_date IS NOT NULL
                        AND sh.delivered_date <= po.required_date
                       THEN 1 ELSE 0
                   END)
            FROM Shipment sh
            JOIN PurchaseOrder po ON po.po_id = sh.po_id
            WHERE sh.supplier_id = ?
        """, (supplier_id,)).fetchone()

        delivery_score = (
            100.0 * delivery[1] / delivery[0]
            if delivery[0] else 50.0
        )

        quality = connection.execute("""
            SELECT SUM(i.accepted_qty), SUM(i.inspected_qty)
            FROM Inspection i
            JOIN Shipment sh ON sh.shipment_id = i.shipment_id
            WHERE sh.supplier_id = ?
        """, (supplier_id,)).fetchone()

        quality_score = (
            100.0 * quality[0] / quality[1]
            if quality[1] else 50.0
        )

        cost = connection.execute("""
            SELECT SUM(ABS(i.variance_amount)), SUM(po.po_total)
            FROM Invoice i
            JOIN PurchaseOrder po ON po.po_id = i.po_id
            WHERE po.supplier_id = ?
        """, (supplier_id,)).fetchone()

        cost_score = (
            100.0 * (1 - cost[0] / cost[1])
            if cost[1] else 50.0
        )

        capacity = connection.execute("""
            SELECT SUM(sh.shipped_qty), SUM(DISTINCT s.capacity_units)
            FROM Shipment sh
            JOIN Site s ON s.site_id = sh.site_id
            WHERE sh.supplier_id = ?
        """, (supplier_id,)).fetchone()

        capacity_score = (
            min(100.0, 100.0 * capacity[1] / capacity[0])
            if capacity[0] and capacity[1] else 50.0
        )

        risk = connection.execute("""
            SELECT COUNT(*),
                   SUM(CASE WHEN severity >= 4 THEN 1 ELSE 0 END)
            FROM RiskSignal
            WHERE supplier_id = ?
        """, (supplier_id,)).fetchone()

        compliance_score = 100.0

        if compliance_status.upper() not in (
            "COMPLIANT", "ACTIVE", "GOOD"
        ):
            compliance_score -= 40.0

        if risk[1]:
            compliance_score -= min(60.0, risk[1] * 5.0)

        if not active:
            compliance_score -= 20.0

        disruption_risk = connection.execute("""
            SELECT COUNT(*), SUM(severity)
            FROM RiskSignal
            WHERE supplier_id = ?
              AND signal_type IN (
                  'WEATHER_DISRUPTION',
                  'GEOPOLITICAL_RISK',
                  'CAPACITY_RISK'
              )
        """, (supplier_id,)).fetchone()

        severity_total = disruption_risk[1] or 0

        disruption_score = max(
            0.0,
            100.0 - severity_total * 2.0
        )

        components = {
            "delivery": clamp(delivery_score),
            "quality": clamp(quality_score),
            "cost": clamp(cost_score),
            "capacity": clamp(capacity_score),
            "compliance": clamp(compliance_score),
            "disruption": clamp(disruption_score),
        }

        final_score = round(sum(
            components[name] * WEIGHTS[name]
            for name in WEIGHTS
        ), 2)

        if final_score >= 85:
            band = "EXCELLENT"
        elif final_score >= 70:
            band = "GOOD"
        elif final_score >= 50:
            band = "AVERAGE"
        else:
            band = "POOR"

        results.append((
            supplier_id,
            date.today().isoformat(),
            components["delivery"],
            components["quality"],
            components["cost"],
            components["capacity"],
            components["compliance"],
            components["disruption"],
            final_score,
            band,
        ))

    return results


def main():
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")

        scores = calculate_scores(connection)

        connection.execute("DELETE FROM SupplierScore")

        connection.executemany("""
            INSERT INTO SupplierScore (
                score_id, supplier_id, as_of_date,
                delivery_score, quality_score, cost_score,
                capacity_score, compliance_score, disruption_score,
                final_score, reliability_band
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (f"SC-{i:06d}", *row)
            for i, row in enumerate(scores, start=1)
        ])

        connection.commit()

        print(f"Calculated scores for {len(scores)} suppliers.")

        print("\nTop 10 suppliers:")
        for row in connection.execute("""
            SELECT supplier_id, final_score, reliability_band
            FROM SupplierScore
            ORDER BY final_score DESC
            LIMIT 10
        """):
            print(row)

        print("\nAverage component scores:")
        averages = connection.execute("""
            SELECT ROUND(AVG(delivery_score), 2),
                   ROUND(AVG(quality_score), 2),
                   ROUND(AVG(cost_score), 2),
                   ROUND(AVG(capacity_score), 2),
                   ROUND(AVG(compliance_score), 2),
                   ROUND(AVG(disruption_score), 2)
            FROM SupplierScore
        """).fetchone()

        print(
            "Delivery, Quality, Cost, Capacity, "
            "Compliance, Disruption:",
            averages,
        )


if __name__ == "__main__":
    main()




from scoring import clamp, WEIGHTS


def test_clamp_limits_scores():
    assert clamp(-10) == 0.0
    assert clamp(120) == 100.0
    assert clamp(50) == 50


def test_weights_sum_to_one():
    assert abs(sum(WEIGHTS.values()) - 1.0) < 1e-9


def test_reliability_band_boundaries():
    def get_band(score):
        if score >= 85:
            return "EXCELLENT"
        elif score >= 70:
            return "GOOD"
        elif score >= 50:
            return "AVERAGE"
        return "POOR"

    assert get_band(85) == "EXCELLENT"
    assert get_band(70) == "GOOD"
    assert get_band(50) == "AVERAGE"
    assert get_band(49.99) == "POOR"


def test_component_scores_are_clamped():
    components = [
        clamp(-5),
        clamp(0),
        clamp(50),
        clamp(100),
        clamp(150),
    ]

    assert all(0 <= score <= 100 for score in components)