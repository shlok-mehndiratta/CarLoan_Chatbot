import sqlite3
import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def create_contracts_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            raw_text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def create_sla_table():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sla_extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            sla_json TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(id)
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_sla_contract_id
        ON sla_extractions(contract_id)
    """)
    conn.commit()
    conn.close()


def save_contract(file_name: str, raw_text: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO contracts (file_name, raw_text) VALUES (?, ?)",
        (file_name, raw_text)
    )
    contract_id = cur.lastrowid
    conn.commit()
    conn.close()
    return contract_id


def save_sla(contract_id: int, sla_data: dict):
    conn = get_connection()
    conn.execute(
        "INSERT INTO sla_extractions (contract_id, sla_json) VALUES (?, ?)",
        (contract_id, json.dumps(sla_data))
    )
    conn.commit()
    conn.close()