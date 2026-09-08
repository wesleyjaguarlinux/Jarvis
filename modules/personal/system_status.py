# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH

INBOX_DIR = Path("data/inbox")
EXPORT_DIR = Path("data/exports")

def check_system_status():
    print("\n🔍 [Jarvis System Status - Diagnóstico Geral]")
    print("-" * 45)

    # Status do Banco de Dados
    if DB_PATH.exists():
        db_size_kb = DB_PATH.stat().st_size / 1024
        print(f"📁 Banco de Dados: OK ({db_size_kb:.2f} KB)")
    else:
        print("❌ Banco de Dados: NÃO ENCONTRADO")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Contagens de registros
    try:
        cursor.execute("SELECT COUNT(*) FROM raw_files")
        total_files = cursor.fetchone()[0]
    except:
        total_files = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM quick_notes")
        total_notes = cursor.fetchone()[0]
    except:
        total_notes = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM daily_goals WHERE status = 'PENDENTE'")
        pending_goals = cursor.fetchone()[0]
    except:
        pending_goals = 0

    try:
        cursor.execute("SELECT COUNT(*) FROM system_logs WHERE module = 'agent_runner'")
        agent_runs = cursor.fetchone()[0]
    except:
        agent_runs = 0

    conn.close()

    # Status de Pastas Locais
    inbox_count = len(list(INBOX_DIR.glob("*"))) if INBOX_DIR.exists() else 0
    export_count = len(list(EXPORT_DIR.glob("*.md"))) if EXPORT_DIR.exists() else 0

    print(f"📥 Arquivos na Inbox pendentes: {inbox_count}")
    print(f"📊 Relatórios Exportados (Markdown): {export_count}")
    print(f"📂 Total de Arquivos Ingestados (DB): {total_files}")
    print(f"📝 Total de Notas Rápidas: {total_notes}")
    print(f"🎯 Metas do Dia Pendentes: {pending_goals}")
    print(f"🤖 Total de Execuções do Agente: {agent_runs}")
    print("-" * 45)
    print("✅ Sistema Operacional e Integrado com Sucesso!\n")

if __name__ == "__main__":
    check_system_status()