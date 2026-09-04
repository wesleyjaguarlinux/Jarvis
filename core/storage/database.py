# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path

DB_PATH = Path("data/jarvis.db")

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS raw_files (
            file_hash TEXT PRIMARY KEY,
            file_type TEXT NOT NULL,
            original_name TEXT NOT NULL,
            stored_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            domain TEXT DEFAULT 'PERSONAL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS processed_content (
            file_hash TEXT PRIMARY KEY,
            extracted_text TEXT,
            FOREIGN KEY (file_hash) REFERENCES raw_files(file_hash)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT,
            transaction_date TEXT,
            description TEXT,
            amount REAL,
            type TEXT,
            domain TEXT DEFAULT 'CORPORATE',
            FOREIGN KEY (file_hash) REFERENCES raw_files(file_hash)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quick_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            tag TEXT DEFAULT 'geral',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_name TEXT NOT NULL,
            status TEXT DEFAULT 'PENDENTE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Banco de dados atualizado com suporte a tags nas notas!")
