"""
Database module — SQLite with full schema for the Car Lease/Loan
Contract Review & Negotiation Assistant.

Tables:
  users, vehicles, vehicle_recalls, dealers,
  contracts, contract_files, extracted_clauses,
  negotiation_threads, negotiation_messages,
  price_sources, price_recommendations, offer_comparisons
"""

import sqlite3
import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


# ──────────────────────────── connection ──────────────────────────── #

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# ──────────────────────────── schema ──────────────────────────── #

_SCHEMA_SQL = """

-- Users
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    email           TEXT UNIQUE,
    phone           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Dealers / Brokers
CREATE TABLE IF NOT EXISTS dealers (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    type            TEXT CHECK(type IN ('dealer', 'broker')) DEFAULT 'dealer',
    address         TEXT,
    phone           TEXT,
    email           TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vehicles
CREATE TABLE IF NOT EXISTS vehicles (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vin             TEXT UNIQUE,
    make            TEXT,
    model           TEXT,
    year            INTEGER,
    trim            TEXT,
    body_class      TEXT,
    engine          TEXT,
    fuel_type       TEXT,
    drive_type      TEXT,
    plant_info      TEXT,
    raw_nhtsa_json  TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vehicle Recalls
CREATE TABLE IF NOT EXISTS vehicle_recalls (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id      INTEGER NOT NULL,
    nhtsa_campaign  TEXT,
    component       TEXT,
    summary         TEXT,
    consequence     TEXT,
    remedy          TEXT,
    report_date     TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Contracts (expanded from original)
CREATE TABLE IF NOT EXISTS contracts (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    dealer_id       INTEGER,
    vehicle_id      INTEGER,
    file_name       TEXT NOT NULL,
    raw_text        TEXT NOT NULL,
    contract_type   TEXT,
    status          TEXT DEFAULT 'analyzed',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id)   REFERENCES users(id),
    FOREIGN KEY (dealer_id) REFERENCES dealers(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);

-- Contract Files (multiple files per contract)
CREATE TABLE IF NOT EXISTS contract_files (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id     INTEGER NOT NULL,
    file_name       TEXT NOT NULL,
    file_path       TEXT,
    file_type       TEXT DEFAULT 'pdf',
    file_size_bytes INTEGER,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);

-- SLA Extractions (kept for backward compatibility)
CREATE TABLE IF NOT EXISTS sla_extractions (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id     INTEGER NOT NULL,
    sla_json        TEXT NOT NULL,
    extraction_method TEXT DEFAULT 'rule_based',
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);
CREATE INDEX IF NOT EXISTS idx_sla_contract_id
    ON sla_extractions(contract_id);

-- Extracted Clauses (individual clauses for fine-grained access)
CREATE TABLE IF NOT EXISTS extracted_clauses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id     INTEGER NOT NULL,
    clause_key      TEXT NOT NULL,
    clause_value    TEXT,
    source          TEXT CHECK(source IN ('rule', 'llm', 'merged')) DEFAULT 'merged',
    confidence      REAL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id)
);
CREATE INDEX IF NOT EXISTS idx_clauses_contract_id
    ON extracted_clauses(contract_id);

-- Negotiation Threads
CREATE TABLE IF NOT EXISTS negotiation_threads (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    contract_id     INTEGER,
    user_id         INTEGER,
    title           TEXT,
    status          TEXT DEFAULT 'active',
    context_json    TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (user_id)     REFERENCES users(id)
);

-- Negotiation Messages
CREATE TABLE IF NOT EXISTS negotiation_messages (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id       INTEGER NOT NULL,
    role            TEXT CHECK(role IN ('user', 'assistant')) NOT NULL,
    content         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (thread_id) REFERENCES negotiation_threads(id)
);
CREATE INDEX IF NOT EXISTS idx_messages_thread_id
    ON negotiation_messages(thread_id);

-- Price Sources
CREATE TABLE IF NOT EXISTS price_sources (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            TEXT NOT NULL,
    source_type     TEXT,
    api_url         TEXT,
    is_active       INTEGER DEFAULT 1,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Price Recommendations
CREATE TABLE IF NOT EXISTS price_recommendations (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    vehicle_id      INTEGER,
    contract_id     INTEGER,
    source_id       INTEGER,
    low_price       REAL,
    market_price    REAL,
    high_price      REAL,
    confidence      REAL,
    data_json       TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id)  REFERENCES vehicles(id),
    FOREIGN KEY (contract_id) REFERENCES contracts(id),
    FOREIGN KEY (source_id)   REFERENCES price_sources(id)
);

-- Offer Comparisons
CREATE TABLE IF NOT EXISTS offer_comparisons (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER,
    name            TEXT,
    contract_ids    TEXT NOT NULL,
    comparison_json TEXT,
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

"""


def init_db():
    """Create all tables. Safe to call multiple times."""
    conn = get_connection()
    conn.executescript(_SCHEMA_SQL)
    conn.commit()
    conn.close()


# Backward-compat aliases
def create_contracts_table():
    init_db()

def create_sla_table():
    init_db()


# ──────────────────────────── CRUD helpers ──────────────────────────── #

# ---- Contracts ----

def save_contract(file_name: str, raw_text: str,
                  user_id: int = None, dealer_id: int = None,
                  vehicle_id: int = None, contract_type: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO contracts
           (file_name, raw_text, user_id, dealer_id, vehicle_id, contract_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (file_name, raw_text, user_id, dealer_id, vehicle_id, contract_type)
    )
    contract_id = cur.lastrowid
    conn.commit()
    conn.close()
    return contract_id


def save_sla(contract_id: int, sla_data: dict,
             extraction_method: str = "rule_based"):
    conn = get_connection()
    conn.execute(
        """INSERT INTO sla_extractions (contract_id, sla_json, extraction_method)
           VALUES (?, ?, ?)""",
        (contract_id, json.dumps(sla_data), extraction_method)
    )
    conn.commit()
    conn.close()


def save_extracted_clauses(contract_id: int, clauses: dict,
                           source: str = "merged"):
    """Save individual clause key-value pairs."""
    conn = get_connection()
    for key, value in clauses.items():
        conn.execute(
            """INSERT INTO extracted_clauses
               (contract_id, clause_key, clause_value, source)
               VALUES (?, ?, ?, ?)""",
            (contract_id, key, json.dumps(value) if not isinstance(value, str) else value, source)
        )
    conn.commit()
    conn.close()


def get_contract(contract_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM contracts WHERE id = ?", (contract_id,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_sla_for_contract(contract_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM sla_extractions WHERE contract_id = ? ORDER BY id DESC LIMIT 1",
        (contract_id,)
    ).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result["sla_json"] = json.loads(result["sla_json"])
        return result
    return None


# ---- Vehicles ----

def save_vehicle(vehicle_data: dict) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT OR IGNORE INTO vehicles
           (vin, make, model, year, trim, body_class, engine,
            fuel_type, drive_type, plant_info, raw_nhtsa_json)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            vehicle_data.get("vin"),
            vehicle_data.get("make"),
            vehicle_data.get("model"),
            vehicle_data.get("year"),
            vehicle_data.get("trim"),
            vehicle_data.get("body_class"),
            vehicle_data.get("engine"),
            vehicle_data.get("fuel_type"),
            vehicle_data.get("drive_type"),
            vehicle_data.get("plant_info"),
            json.dumps(vehicle_data.get("raw_nhtsa", {})),
        )
    )
    # If INSERT OR IGNORE skipped, fetch existing id
    if cur.lastrowid == 0:
        row = conn.execute(
            "SELECT id FROM vehicles WHERE vin = ?",
            (vehicle_data.get("vin"),)
        ).fetchone()
        vehicle_id = row["id"] if row else 0
    else:
        vehicle_id = cur.lastrowid
    conn.commit()
    conn.close()
    return vehicle_id


def save_vehicle_recalls(vehicle_id: int, recalls: list):
    conn = get_connection()
    for recall in recalls:
        conn.execute(
            """INSERT INTO vehicle_recalls
               (vehicle_id, nhtsa_campaign, component, summary,
                consequence, remedy, report_date)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                vehicle_id,
                recall.get("nhtsa_campaign"),
                recall.get("component"),
                recall.get("summary"),
                recall.get("consequence"),
                recall.get("remedy"),
                recall.get("report_date"),
            )
        )
    conn.commit()
    conn.close()


# ---- Negotiation ----

def create_negotiation_thread(contract_id: int, context_json: str = None,
                              user_id: int = None, title: str = None) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO negotiation_threads
           (contract_id, user_id, title, context_json)
           VALUES (?, ?, ?, ?)""",
        (contract_id, user_id, title, context_json)
    )
    thread_id = cur.lastrowid
    conn.commit()
    conn.close()
    return thread_id


def save_negotiation_message(thread_id: int, role: str, content: str):
    conn = get_connection()
    conn.execute(
        """INSERT INTO negotiation_messages (thread_id, role, content)
           VALUES (?, ?, ?)""",
        (thread_id, role, content)
    )
    conn.commit()
    conn.close()


def get_negotiation_history(thread_id: int) -> list:
    conn = get_connection()
    rows = conn.execute(
        """SELECT role, content, created_at
           FROM negotiation_messages
           WHERE thread_id = ?
           ORDER BY id ASC""",
        (thread_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Price Recommendations ----

def save_price_recommendation(vehicle_id: int = None, contract_id: int = None,
                               source: str = "depreciation_model",
                               result: dict = None) -> int:
    """Save a price estimation result to the database."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO price_recommendations
           (vehicle_id, contract_id, low_price, market_price, high_price,
            confidence, data_json)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            vehicle_id,
            contract_id,
            result.get("low_price") if result else None,
            result.get("market_price") if result else None,
            result.get("high_price") if result else None,
            result.get("confidence") if result else None,
            json.dumps(result) if result else None,
        )
    )
    rec_id = cur.lastrowid
    conn.commit()
    conn.close()
    return rec_id


def get_price_recommendations(vehicle_id: int = None, contract_id: int = None) -> list:
    """Retrieve price recommendations, filtered by vehicle or contract."""
    conn = get_connection()
    if vehicle_id:
        rows = conn.execute(
            "SELECT * FROM price_recommendations WHERE vehicle_id = ? ORDER BY id DESC",
            (vehicle_id,)
        ).fetchall()
    elif contract_id:
        rows = conn.execute(
            "SELECT * FROM price_recommendations WHERE contract_id = ? ORDER BY id DESC",
            (contract_id,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM price_recommendations ORDER BY id DESC LIMIT 20"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]