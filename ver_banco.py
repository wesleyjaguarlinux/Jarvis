import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH

print(f"Caminho oficial do banco: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Cria a tabela time_blocks no banco oficial se ela não existir
cursor.execute('''
    CREATE TABLE IF NOT EXISTS time_blocks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        block_date DATE,
        start_time TEXT,
        end_time TEXT,
        activity_category TEXT,
        description TEXT,
        interruptions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tabelas atualizadas no banco oficial:", tables)

print("\n--- REGISTROS DE TIME_BLOCKS ---")
cursor.execute("SELECT * FROM time_blocks;")
rows = cursor.fetchall()
if not rows:
    print("A tabela 'time_blocks' está ativa e pronta, mas ainda sem registros.")
else:
    for row in rows:
        print(row)

conn.close()
