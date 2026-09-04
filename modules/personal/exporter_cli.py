# -*- coding: utf-8 -*-
import os
import sqlite3
from pathlib import Path
from datetime import datetime
from core.storage.database import DB_PATH
from core.storage.logger import log_event

EXPORT_DIR = Path("data/exports")

def export_to_markdown():
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados não encontrado.")
        return

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_path = EXPORT_DIR / f"jarvis_report_{timestamp}.md"

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Coleta dados com tratamento caso tabelas variem
    try:
        cursor.execute("SELECT domain, COUNT(*) FROM raw_files GROUP BY domain")
        files_data = cursor.fetchall()
    except:
        files_data = []

    try:
        cursor.execute("SELECT tag, content, created_at FROM quick_notes ORDER BY created_at DESC")
        notes_data = cursor.fetchall()
    except:
        notes_data = []

    try:
        # Tenta buscar na tabela de hábitos padrão
        cursor.execute("SELECT id, habit_name, status FROM habits_list")
        habits_data = cursor.fetchall()
    except:
        try:
            cursor.execute("SELECT id, habit_name, status FROM habits")
            habits_data = cursor.fetchall()
        except:
            habits_data = []

    conn.close()

    # Monta o conteúdo Markdown
    md_content = f"""# 🧠 Jarvis Life OS - Relatório Exportado
Gerado em: {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}

## 📂 Arquivos Ingestados por Domínio
"""
    for domain, count in files_data:
        md_content += f"- **{domain}**: {count} arquivo(s)\n"

    md_content += "\n## 📝 Notas Rápidas e Conhecimento Web\n"
    for tag, content, created_at in notes_data:
        md_content += f"- **[#{tag}]** {content} *({created_at})*\n"

    md_content += "\n## 🎯 Status de Hábitos e Metas\n"
    for habit_id, name, status in habits_data:
        icon = "✅" if status == "CONCLUIDO" else "⏳"
        md_content += f"- {icon} [{habit_id}] {name} - **{status}**\n"

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    log_event("INFO", "exporter_cli", f"Relatório exportado para {file_path.name}")
    print(f"✅ [Jarvis Export] Relatório gerado com sucesso em: {file_path}")

if __name__ == "__main__":
    export_to_markdown()