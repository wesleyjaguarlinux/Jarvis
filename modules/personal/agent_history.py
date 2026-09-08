# -*- coding: utf-8 -*-
import sqlite3
from core.storage.database import DB_PATH

def list_agent_history():
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT level, module, message, created_at FROM system_logs WHERE module = 'agent_runner' ORDER BY id DESC LIMIT 10")
        logs = cursor.fetchall()
    except Exception as e:
        print(f"❌ Erro ao consultar histórico: {e}")
        logs = []

    conn.close()

    print("\n🤖 [Jarvis Agent History - Últimas Execuções]")
    if logs:
        for level, module, message, created_at in logs:
            print(f"  - [{created_at}] ({level}) {message}")
    else:
        print("  (Nenhum registro de execução do agente encontrado)")
    print()

if __name__ == "__main__":
    list_agent_history()