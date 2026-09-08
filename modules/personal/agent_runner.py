# -*- coding: utf-8 -*-
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from core.storage.database import DB_PATH
from core.storage.logger import log_event

def run_local_agent():
    print("🤖 [Jarvis Agent] Iniciando varredura e execução de tarefas autônomas...")
    
    if not DB_PATH.exists():
        print("❌ [Jarvis Agent] Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Exemplo de ação autônoma do agente: verifica metas pendentes do dia e otimiza registros
    cursor.execute("SELECT COUNT(*) FROM daily_goals WHERE status = 'PENDENTE'")
    pending_goals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM raw_files")
    total_files = cursor.fetchone()[0]

    conn.close()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary_msg = f"Varredura concluída em {timestamp}. Metas pendentes: {pending_goals} | Total de arquivos ingestados: {total_files}"
    
    log_event("INFO", "agent_runner", summary_msg)
    print(f"✅ [Jarvis Agent] {summary_msg}")

if __name__ == "__main__":
    run_local_agent()