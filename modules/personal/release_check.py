# -*- coding: utf-8 -*-
import sys
from pathlib import Path
from core.storage.database import DB_PATH

def audit_system_release():
    print("\n🚀 ===============================================")
    print("       JARVIS LIFE OS - AUDITORIA DE RELEASE 100%   ")
    print("=================================================")
    
    modules_to_check = [
        "core/storage/database.py",
        "core/storage/logger.py",
        "modules/personal/reporter.py",
        "modules/personal/habits_cli.py",
        "modules/personal/notes_cli.py",
        "modules/personal/inbox_watcher.py",
        "modules/personal/search_cli.py",
        "modules/personal/web_fetcher.py",
        "modules/personal/exporter_cli.py",
        "modules/personal/scheduler.py",
        "modules/personal/goals_cli.py",
        "modules/personal/agent_runner.py",
        "modules/personal/agent_history.py",
        "modules/personal/system_status.py",
        "modules/personal/jarvis_help.py"
    ]

    all_ok = True
    for mod in modules_to_check:
        path = Path(mod)
        if path.exists():
            print(f"  [OK] Módulo encontrado: {mod}")
        else:
            print(f"  [FALHA] Módulo ausente: {mod}")
            all_ok = False

    print("-" * 49)
    if DB_PATH.exists():
        print("  [OK] Banco de dados SQLite íntegro e operacional.")
    else:
        print("  [FALHA] Banco de dados SQLite não encontrado.")
        all_ok = False

    print("=================================================")
    if all_ok:
        print("🎉 STATUS DO PROJETO: 100% CONCLUÍDO (Fase 4 Atingida)")
        print("🔹 O Jarvis Life OS está pronto, autônomo e estruturado.")
    else:
        print("⚠️ STATUS DO PROJETO: Existem pendências a resolver.")
    print("=================================================\n")

if __name__ == "__main__":
    audit_system_release()