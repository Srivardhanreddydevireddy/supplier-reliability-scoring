
PRAGMA foreign_keys = ON;

CREATE TABLE Supplier (
    supplier_id TEXT PRIMARY KEY,
    supplier_name TEXT NOT NULL,
    supplier_tier TEXT NOT NULL,
    country TEXT NOT NULL,
    compliance_status TEXT NOT NULL,
    active INTEGER NOT NULL
);

CREATE TABLE Site (
    site_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    site_name TEXT NOT NULL,
    country TEXT NOT NULL,
    capacity_units INTEGER NOT NULL,
    FOREIGN KEY (supplier_id)
        REFERENCES Supplier(supplier_id)
);

CREATE TABLE Contract (
    contract_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    contract_status TEXT NOT NULL,
    FOREIGN KEY (supplier_id)
        REFERENCES Supplier(supplier_id)
);

CREATE TABLE PurchaseOrder (
    po_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    contract_id TEXT NOT NULL,
    po_date TEXT NOT NULL,
    required_date TEXT NOT NULL,
    po_total REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (supplier_id)
        REFERENCES Supplier(supplier_id),
    FOREIGN KEY (site_id)
        REFERENCES Site(site_id),
    FOREIGN KEY (contract_id)
        REFERENCES Contract(contract_id)
);

CREATE TABLE POLine (
    po_line_id TEXT PRIMARY KEY,
    po_id TEXT NOT NULL,
    line_number INTEGER NOT NULL,
    sku TEXT NOT NULL,
    ordered_qty INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL,
    FOREIGN KEY (po_id)
        REFERENCES PurchaseOrder(po_id),
    UNIQUE (po_id, line_number)
);

CREATE TABLE Shipment (
    shipment_id TEXT PRIMARY KEY,
    po_id TEXT NOT NULL,
    supplier_id TEXT NOT NULL,
    site_id TEXT NOT NULL,
    dispatch_date TEXT NOT NULL,
    delivered_date TEXT,
    shipped_qty INTEGER NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (po_id)
        REFERENCES PurchaseOrder(po_id),
    FOREIGN KEY (supplier_id)
        REFERENCES Supplier(supplier_id),
    FOREIGN KEY (site_id)
        REFERENCES Site(site_id)
);

CREATE TABLE DeliveryEvent (
    delivery_event_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_time TEXT NOT NULL,
    source TEXT NOT NULL,
    FOREIGN KEY (shipment_id)
        REFERENCES Shipment(shipment_id)
);

CREATE TABLE Inspection (
    inspection_id TEXT PRIMARY KEY,
    shipment_id TEXT NOT NULL,
    inspected_qty INTEGER NOT NULL,
    accepted_qty INTEGER NOT NULL,
    rejected_qty INTEGER NOT NULL,
    result TEXT NOT NULL,
    FOREIGN KEY (shipment_id)
        REFERENCES Shipment(shipment_id)
);

CREATE TABLE Invoice (
    invoice_id TEXT PRIMARY KEY,
    po_id TEXT NOT NULL,
    invoice_amount REAL NOT NULL,
    variance_amount REAL NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (po_id)
        REFERENCES PurchaseOrder(po_id)
);

CREATE TABLE RiskSignal (
    risk_signal_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    severity INTEGER NOT NULL,
    source TEXT,
    signal_time TEXT,
    FOREIGN KEY (supplier_id)
        REFERENCES Supplier(supplier_id)
);

CREATE TABLE SupplierScore (
    score_id TEXT PRIMARY KEY,
    supplier_id TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    delivery_score REAL,
    quality_score REAL,
    cost_score REAL,
    capacity_score REAL,
    compliance_score REAL,
    disruption_score REAL,
    final_score REAL,
    reliability_band TEXT NOT NULL,
    FOREIGN KEY (supplier_id)
        REFERENCES Supplier(supplier_id)
);