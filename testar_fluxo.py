import sqlite3
from datetime import date
from core.storage.database import DB_PATH

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Insere um bloco de teste para hoje
today_str = date.today().strftime("%Y-%m-%d")
cursor.execute('''
    INSERT INTO time_blocks (block_date, start_time, end_time, activity_category, description, interruptions) 
    VALUES (?, '14:00', '15:30', 'cozinha', '1 massa de brigadeiro (800g) e 1 de ninho (700g)', '15 min no celular')
''', (today_str,))
conn.commit()

# Executa o compilador
cursor.execute("SELECT start_time, end_time, activity_category, description, interruptions FROM time_blocks WHERE block_date = ? ORDER BY start_time ASC", (today_str,))
rows = cursor.fetchall()
conn.close()

print("--- SIMULAÇÃO DE RELATÓRIO PARA O OBSIDIAN ---")
print(f"# 📝 REGISTRO DIÁRIO DE EXECUÇÃO — [{today_str}]\n")
print("## ⏱️ 1. Linha do Tempo e Blocos de Produção")
for st, et, cat, desc, intr in rows:
    print(f"- **[{st} - {et}] ({cat.upper()}):** {desc} | *Gargalo/Intervalo:* {intr}")
