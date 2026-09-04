# -*- coding: utf-8 -*-
import sqlite3
from core.storage.database import DB_PATH
from core.storage.logger import log_event

class MoneyFlowReporter:
    def __init__(self):
        pass

    def generate_summary(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        try:
            cursor.execute("SELECT COUNT(*), SUM(amount), type FROM financial_transactions GROUP BY type")
            results = cursor.fetchall()
            
            cursor.execute("SELECT t.transaction_date, t.description, t.amount, t.type, r.original_name FROM financial_transactions t JOIN raw_files r ON t.file_hash = r.file_hash")
            transactions = cursor.fetchall()
        except sqlite3.OperationalError:
            results = []
            transactions = []
        finally:
            conn.close()

        log_event("INFO", "moneyflow_reporter", "Relatório financeiro gerado com sucesso.")
        
        print("\n[MoneyFlow - Resumo Executivo]")
        if not transactions:
            print("Nenhuma transação financeira registrada na base.")
            return

        print("Transações Registradas:")
        for tx in transactions:
            print(f"  - [{tx[0]}] {tx[1]} | R$ {tx[2]:.2f} ({tx[3]}) [Origem: {tx[4]}]")
            
        print("\nConsolidado por Tipo:")
        for res in results:
            print(f"  - {res[2]}: {res[0]} transação(ões) | Total: R$ {res[1]:.2f}")

if __name__ == "__main__":
    reporter = MoneyFlowReporter()
    reporter.generate_summary()
