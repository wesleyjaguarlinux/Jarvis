# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH
from core.storage.logger import log_event

class ProductivityReporter:
    def __init__(self):
        pass

    def generate_report(self):
        if not DB_PATH.exists():
            print("[Jarvis Reporter] Banco de dados não encontrado.")
            return

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        # 1. Estatísticas de Arquivos e Domínios
        cursor.execute("SELECT domain, COUNT(*) FROM raw_files GROUP BY domain")
        files_by_domain = cursor.fetchall()

        # 2. Estatísticas de Notas Rápidas por Tag
        cursor.execute("SELECT tag, COUNT(*) FROM quick_notes GROUP BY tag")
        notes_by_tag = cursor.fetchall()

        # 3. Estatísticas de Hábitos e Metas
        cursor.execute("SELECT status, COUNT(*) FROM personal_habits GROUP BY status")
        habits_status = cursor.fetchall()

        # 4. Últimas 3 notas inseridas
        cursor.execute("SELECT content, tag, created_at FROM quick_notes ORDER BY created_at DESC LIMIT 3")
        recent_notes = cursor.fetchall()

        conn.close()

        print("\n" + "="*50)
        print(" 🧠 JARVIS LIFE OS - RELATÓRIO DE PRODUTIVIDADE")
        print("="*50)

        print("\n📂 [Arquivos Ingestados por Domínio]")
        if not files_by_domain:
            print("  Nenhum arquivo registrado.")
        else:
            for domain, count in files_by_domain:
                print(f"  - {domain}: {count} arquivo(s)")

        print("\n📝 [Notas Rápidas por Tag]")
        if not notes_by_tag:
            print("  Nenhuma nota registrada.")
        else:
            for tag, count in notes_by_tag:
                print(f"  - #{tag}: {count} nota(s)")

        print("\n🎯 [Status de Metas e Hábitos]")
        if not habits_status:
            print("  Nenhuma meta registrada.")
        else:
            for status, count in habits_status:
                print(f"  - {status}: {count}")

        print("\n📌 [Últimas Notas Capturadas]")
        if not recent_notes:
            print("  Nenhuma nota recente.")
        else:
            for note in recent_notes:
                print(f"  - [{note[1].upper()}] {note[0]} ({note[2]})")

        print("="*50 + "\n")
        log_event("INFO", "reporter", "Relatório de produtividade gerado com sucesso.")

if __name__ == "__main__":
    reporter = ProductivityReporter()
    reporter.generate_report()
