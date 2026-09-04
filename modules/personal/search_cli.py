# -*- coding: utf-8 -*-
import sys
import argparse
import sqlite3
from core.storage.database import DB_PATH

def search_database(term: str):
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    search_pattern = f"%{term}%"

    print(f"\n🔍 [Jarvis Search] Resultados para o termo: '{term}'\n")

    # Busca em Notas Rápidas
    cursor.execute("SELECT tag, content, created_at FROM quick_notes WHERE content LIKE ? OR tag LIKE ?", (search_pattern, search_pattern))
    notes = cursor.fetchall()
    
    print("📝 [Notas Rápidas Encontradas]")
    if notes:
        for tag, content, created_at in notes:
            print(f"  - #{tag}: {content} ({created_at})")
    else:
        print("  (Nenhuma nota correspondente)")

    # Busca em Arquivos Ingestados
    cursor.execute("SELECT original_name, domain, created_at FROM raw_files WHERE original_name LIKE ? OR domain LIKE ?", (search_pattern, search_pattern))
    files = cursor.fetchall()

    print("\n📂 [Arquivos Ingestados Encontrados]")
    if files:
        for original_name, domain, created_at in files:
            print(f"  - [{domain}] {original_name} ({created_at})")
    else:
        print("  (Nenhum arquivo correspondente)")

    print()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        search_database(sys.argv[1])
    else:
        print("⚠️ Uso: python -m modules.personal.search_cli <termo>")