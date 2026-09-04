# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH
from core.storage.logger import log_event

def init_finance_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS financial_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_hash TEXT,
            transaction_date TEXT,
            description TEXT,
            amount REAL,
            type TEXT,
            FOREIGN KEY (file_hash) REFERENCES raw_files(file_hash)
        )
    ''')
    conn.commit()
    conn.close()

class FinanceParser:
    def __init__(self):
        init_finance_table()

    def parse_simulated_extrato(self, file_hash: str, text_content: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        lines = text_content.splitlines()
        count = 0
        for line in lines:
            # Se a linha contiver texto relevante, criamos uma transação padrão de exemplo
            if len(line.strip()) > 0:
                cursor.execute('''
                    INSERT INTO financial_transactions (file_hash, transaction_date, description, amount, type)
                    VALUES (?, ?, ?, ?, ?)
                ''', (file_hash, "2026-09-03", line.strip(), 250.00, "ENTRADA"))
                count += 1

        conn.commit()
        conn.close()
        log_event("INFO", "finance_parser", f"Processadas {count} transações financeiras para o hash {file_hash[:12]}")
        print(f"Parser financeiro executado: {count} registro(s) estruturado(s) no banco.")

if __name__ == "__main__":
    parser = FinanceParser()
    print("Módulo FinanceParser atualizado com sucesso!")
