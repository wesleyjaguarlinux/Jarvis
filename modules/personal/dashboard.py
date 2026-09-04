# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH

def show_dashboard():
    if not DB_PATH.exists():
        print("[Jarvis Dashboard] Banco de dados ainda não inicializado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Contagem de arquivos pessoais
    cursor.execute("SELECT COUNT(*), SUM(file_size) FROM raw_files WHERE domain = 'PERSONAL'")
    file_count, total_bytes = cursor.fetchone()
    total_bytes = total_bytes or 0
    total_kb = total_bytes / 1024

    # Contagem de notas rápidas
    cursor.execute("SELECT COUNT(*) FROM quick_notes")
    notes_count = cursor.fetchone()[0]

    # Contagem de textos indexados
    cursor.execute("SELECT COUNT(*) FROM processed_content")
    indexed_count = cursor.fetchone()[0]

    conn.close()

    print("\n" + "="*40)
    print("       JARVIS LIFE OS - DASHBOARD PESSOAL")
    print("="*40)
    print(f"  📂 Arquivos Ingeridos (Personal): {file_count or 0}")
    print(f"  💾 Espaço Utilizado: {total_kb:.2f} KB")
    print(f"  📝 Notas Rápidas Registradas: {notes_count}")
    print(f"  🔍 Documentos Textuais Indexados: {indexed_count}")
    print("="*40 + "\n")

if __name__ == "__main__":
    show_dashboard()
