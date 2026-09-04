# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH

def init_audit_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            level TEXT NOT NULL,
            module TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def log_event(level: str, module: str, message: str):
    init_audit_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO system_logs (level, module, message)
            VALUES (?, ?, ?)
        ''', (level.upper(), module, message))
        conn.commit()
    finally:
        conn.close()

if __name__ == "__main__":
    init_audit_table()
    log_event("INFO", "logger", "Tabela de auditoria do Jarvis inicializada com sucesso.")
    print("Módulo de logs validado e registrado no SQLite!")
