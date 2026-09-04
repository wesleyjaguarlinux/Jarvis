# -*- coding: utf-8 -*-
import sqlite3
import sys
from pathlib import Path
from core.storage.database import DB_PATH

def search_content(query: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Busca por texto extraído ou nome original do arquivo no domínio pessoal
    cursor.execute('''
        SELECT r.original_name, r.file_type, p.extracted_text 
        FROM processed_content p
        JOIN raw_files r ON p.file_hash = r.file_hash
        WHERE (r.domain = 'PERSONAL' OR r.domain IS NULL) 
        AND (p.extracted_text LIKE ? OR r.original_name LIKE ?)
    ''', (f"%{query}%", f"%{query}%"))
    
    results = cursor.fetchall()
    conn.close()
    
    print(f"\n[Jarvis Search] Resultados para o termo: '{query}'")
    if not results:
        print("Nenhum registro encontrado na base pessoal.")
        return

    for idx, (name, f_type, text) in enumerate(results, 1):
        print(f"\n{idx}. Arquivo: {name} ({f_type})")
        snippet = text.replace('\n', ' ')[:150]
        print(f"   Trecho: {snippet}...")

if __name__ == "__main__":
    term = sys.argv[1] if len(sys.argv) > 1 else "teste"
    search_content(term)
