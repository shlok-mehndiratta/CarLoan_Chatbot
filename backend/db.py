import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def create_contracts_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            raw_text TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_contract(file_name: str, raw_text: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO contracts (file_name, raw_text) VALUES (?, ?)",
        (file_name, raw_text)
    )
    conn.commit()
    conn.close()

def create_sla_table():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sla_extractions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER,
            sla_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (contract_id) REFERENCES contracts(id)
        )
    """)
    conn.commit()
    conn.close()


def save_sla(contract_id: int, sla_json: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sla_extractions (contract_id, sla_json) VALUES (?, ?)",
        (contract_id, sla_json)
    )
    conn.commit()
    conn.close()