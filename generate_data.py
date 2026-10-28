
import csv
import random
from pathlib import Path
from datetime import date, timedelta

SEED = 42
random.seed(SEED)

OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)


def save_csv(filename, rows):
    with (OUTPUT_DIR / filename).open(
        "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {filename}: {len(rows)} records")


suppliers = []
sites = []
countries = ["IN", "US", "DE", "SG", "JP", "VN"]

for i in range(1, 1001):
    sid = f"SUP-{i:06d}"

    suppliers.append({
        "supplier_id": sid,
        "supplier_name": f"Supplier {i:04d}",
        "supplier_tier": random.choice(
            ["STRATEGIC", "PREFERRED", "STANDARD"]
        ),
        "country": random.choice(countries),
        "compliance_status": random.choice(
            ["COMPLIANT", "REVIEW", "EXPIRED"]
        ),
        "active": random.choice([1, 1, 1, 0]),
    })

    for j in range(1, 3):
        sites.append({
            "site_id": f"SITE-{i:06d}-{j:02d}",
            "supplier_id": sid,
            "site_name": f"Supplier {i:04d} Site {j}",
            "country": random.choice(countries),
            "capacity_units": random.randint(500, 10000),
        })


contracts = []

for i in range(1, 1001):
    contracts.append({
        "contract_id": f"CTR-{i:06d}",
        "supplier_id": f"SUP-{i:06d}",
        "start_date": "2025-01-01",
        "end_date": "2027-12-31",
        "contract_status": random.choice(
            ["ACTIVE", "ACTIVE", "EXPIRED"]
        ),
    })


purchase_orders = []
po_lines = []
start_date = date(2025, 1, 1)

for i in range(1, 10001):
    supplier_number = random.randint(1, 1000)
    sid = f"SUP-{supplier_number:06d}"
    site_id = f"SITE-{supplier_number:06d}-{random.randint(1, 2):02d}"

    po_date = start_date + timedelta(days=random.randint(0, 600))
    due_date = po_date + timedelta(days=random.randint(7, 45))
    quantity = random.randint(10, 500)
    price = round(random.uniform(2, 250), 2)
    total = round(quantity * price, 2)
    po_id = f"PO-{i:06d}"

    purchase_orders.append({
        "po_id": po_id,
        "supplier_id": sid,
        "site_id": site_id,
        "contract_id": f"CTR-{supplier_number:06d}",
        "po_date": po_date.isoformat(),
        "required_date": due_date.isoformat(),
        "po_total": total,
        "status": random.choice(["OPEN", "PARTIAL", "CLOSED"]),
    })

    po_lines.append({
        "po_line_id": f"POL-{i:06d}",
        "po_id": po_id,
        "line_number": 1,
        "sku": f"SKU-{random.randint(1, 250):04d}",
        "ordered_qty": quantity,
        "unit_price": price,
        "line_total": total,
    })


shipments = []
delivery_events = []

for i in range(1, 15001):
    po = random.choice(purchase_orders)
    po_date = date.fromisoformat(po["po_date"])
    due_date = date.fromisoformat(po["required_date"])

    dispatch_date = po_date + timedelta(
        days=random.randint(1, max(2, (due_date - po_date).days))
    )

    delivered_date = due_date + timedelta(
        days=random.randint(-5, 10)
    )

    if delivered_date < dispatch_date:
        delivered_date = dispatch_date

    shipment_id = f"SHP-{i:06d}"
    shipped_qty = random.randint(5, 300)

    shipments.append({
        "shipment_id": shipment_id,
        "po_id": po["po_id"],
        "supplier_id": po["supplier_id"],
        "site_id": po["site_id"],
        "dispatch_date": dispatch_date.isoformat(),
        "delivered_date": delivered_date.isoformat(),
        "shipped_qty": shipped_qty,
        "status": "DELIVERED",
    })

    delivery_events.append({
        "delivery_event_id": f"DEV-{i:06d}-1",
        "shipment_id": shipment_id,
        "event_type": "DISPATCHED",
        "event_time": dispatch_date.isoformat() + "T09:00:00",
        "source": "synthetic_carrier",
    })

    delivery_events.append({
        "delivery_event_id": f"DEV-{i:06d}-2",
        "shipment_id": shipment_id,
        "event_type": "DELIVERED",
        "event_time": delivered_date.isoformat() + "T16:00:00",
        "source": "synthetic_carrier",
    })


inspections = []

for i in range(1, 20001):
    shipment = random.choice(shipments)

    inspected_qty = random.randint(
        1, shipment["shipped_qty"]
    )

    rejected_qty = random.randint(
        0, min(10, inspected_qty)
    )

    accepted_qty = inspected_qty - rejected_qty

    inspections.append({
        "inspection_id": f"INSP-{i:06d}",
        "shipment_id": shipment["shipment_id"],
        "inspected_qty": inspected_qty,
        "accepted_qty": accepted_qty,
        "rejected_qty": rejected_qty,
        "result": (
            "PASS"
            if rejected_qty / inspected_qty <= 0.05
            else "FAIL"
        ),
    })

invoices = []

for i in range(1, 12001):
    po = random.choice(purchase_orders)

    po_total = po["po_total"]

    if random.random() < 0.85:
        variance = round(
            po_total * random.uniform(-0.02, 0.02), 2
        )
    else:
        variance = round(
            po_total * random.uniform(-0.15, 0.15), 2
        )

    invoice_amount = round(po_total + variance, 2)

    invoices.append({
        "invoice_id": f"INV-{i:06d}",
        "po_id": po["po_id"],
        "invoice_amount": invoice_amount,
        "variance_amount": variance,
        "status": random.choice(
            ["PAID", "PENDING", "OVERDUE", "DISPUTED"]
        ),
    })

risk_signals = []

signal_types = [
    "FINANCIAL_RISK",
    "GEOPOLITICAL_RISK",
    "WEATHER_DISRUPTION",
    "COMPLIANCE_ISSUE",
    "CYBER_RISK",
    "CAPACITY_RISK",
]

risk_sources = [
    "NEWS",
    "INTERNAL_REPORT",
    "REGULATORY_ALERT",
    "RISK_MONITOR",
]

for i in range(1, 8001):
    supplier = random.choice(suppliers)

    risk_signals.append({
        "risk_signal_id": f"RS-{i:06d}",
        "supplier_id": supplier["supplier_id"],
        "signal_type": random.choice(signal_types),
        "severity": random.randint(1, 5),
        "source": random.choice(risk_sources),
        "signal_time": (
            date.today() - timedelta(days=random.randint(0, 365))
        ).isoformat(),
    })
supplier_scores = []

for i, supplier in enumerate(suppliers, start=1):
    delivery_score = round(random.uniform(40, 100), 2)
    quality_score = round(random.uniform(40, 100), 2)
    cost_score = round(random.uniform(40, 100), 2)
    capacity_score = round(random.uniform(40, 100), 2)
    compliance_score = round(random.uniform(40, 100), 2)
    disruption_score = round(random.uniform(40, 100), 2)

    final_score = round(
        delivery_score * 0.25
        + quality_score * 0.25
        + cost_score * 0.15
        + capacity_score * 0.10
        + compliance_score * 0.15
        + disruption_score * 0.10,
        2,
    )

    if final_score >= 85:
        reliability_band = "EXCELLENT"
    elif final_score >= 70:
        reliability_band = "GOOD"
    elif final_score >= 50:
        reliability_band = "AVERAGE"
    else:
        reliability_band = "POOR"

    supplier_scores.append({
        "score_id": f"SC-{i:06d}",
        "supplier_id": supplier["supplier_id"],
        "as_of_date": date.today().isoformat(),
        "delivery_score": delivery_score,
        "quality_score": quality_score,
        "cost_score": cost_score,
        "capacity_score": capacity_score,
        "compliance_score": compliance_score,
        "disruption_score": disruption_score,
        "final_score": final_score,
        "reliability_band": reliability_band,
    })

save_csv("Supplier.csv", suppliers)
save_csv("Site.csv", sites)
save_csv("Contract.csv", contracts)
save_csv("PurchaseOrder.csv", purchase_orders)
save_csv("POLine.csv", po_lines)
save_csv("Shipment.csv", shipments)
save_csv("DeliveryEvent.csv", delivery_events)
save_csv("Inspection.csv", inspections)
save_csv("Invoice.csv", invoices)
save_csv("RiskSignal.csv", risk_signals)
save_csv("SupplierScore.csv", supplier_scores)
print("Master data generation completed!")