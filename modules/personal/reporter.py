# -*- coding: utf-8 -*-
import sqlite3
from core.storage.database import DB_PATH

def generate_report():
    if not DB_PATH.exists():
        print("[Jarvis Reporter] Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("=" * 50)
    print("  🧠 JARVIS LIFE OS - RELATÓRIO DE PRODUTIVIDADE")
    print("=" * 50)

    # 1. Arquivos Ingestados por Domínio
    print("\n📂 [Arquivos Ingestados por Domínio]")
    cursor.execute("SELECT domain, COUNT(*) FROM raw_files GROUP BY domain")
    files_result = cursor.fetchall()
    if files_result:
        for domain, count in files_result:
            print(f"  - {domain}: {count} arquivo(s)")
    else:
        print("  - Nenhum arquivo ingestado.")

    # 2. Notas Rápidas por Tag
    print("\n📝 [Notas Rápidas por Tag]")
    cursor.execute("SELECT tag, COUNT(*) FROM quick_notes GROUP BY tag")
    notes_result = cursor.fetchall()
    if notes_result:
        for tag, count in notes_result:
            print(f"  - #{tag}: {count} nota(s)")
    else:
        print("  - Nenhuma nota rápida registrada.")

    # 3. Status de Metas e Hábitos (Separando PENDENTE e CONCLUIDO)
    print("\n🎯 [Status de Metas e Hábitos]")
    cursor.execute("SELECT status, COUNT(*) FROM personal_habits GROUP BY status")
    habits_result = cursor.fetchall()
    if habits_result:
        for status, count in habits_result:
            print(f"  - {status}: {count}")
    else:
        print("  - Nenhum hábito ou meta cadastrado.")

    # 4. Últimas Notas Capturadas
    print("\n📌 [Últimas Notas Capturadas]")
    cursor.execute("SELECT tag, content, created_at FROM quick_notes ORDER BY created_at DESC LIMIT 3")
    recent_notes = cursor.fetchall()
    if recent_notes:
        for tag, content, created_at in recent_notes:
            print(f"  - [{tag.upper()}] {content} ({created_at})")
    else:
        print("  - Nenhuma nota recente.")

    print("=" * 50)
    conn.close()

if __name__ == "__main__":
    generate_report()