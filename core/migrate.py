# -*- coding: utf-8 -*-
import sqlite3
from core.storage.database import DB_PATH

def migrate():
    if not DB_PATH.exists():
        print("Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute("ALTER TABLE quick_notes ADD COLUMN domain TEXT DEFAULT 'PERSONAL';")
        conn.commit()
        print("✅ Coluna 'domain' adicionada com sucesso na tabela quick_notes!")
    except sqlite3.OperationalError as e:
        print(f"ℹ️ Nota: {e} (A coluna já pode existir).")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()