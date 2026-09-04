# -*- coding: utf-8 -*-
import os
import sqlite3
import hashlib
from pathlib import Path
from core.storage.database import DB_PATH
from core.storage.logger import log_event

INBOX_DIR = Path("data/inbox")

def calculate_hash(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()

def process_inbox():
    if not INBOX_DIR.exists():
        INBOX_DIR.mkdir(parents=True, exist_ok=True)
        print(f"📁 [Jarvis] Pasta criada: {INBOX_DIR}. Coloque arquivos lá para ingestão.")
        return

    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados não encontrado.")
        return

    files = [f for f in INBOX_DIR.iterdir() if f.is_file()]
    
    if not files:
        print("📂 [Jarvis Inbox] Nenhum arquivo novo encontrado na pasta inbox.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    count = 0
    new_files = []
    for file_path in files:
        file_name = file_path.name
        stored_path = str(file_path)
        file_size = file_path.stat().st_size
        file_type = file_path.suffix.lstrip('.')
        file_hash = calculate_hash(file_path)
        domain = "PERSONAL"
        
        cursor.execute("SELECT file_hash FROM raw_files WHERE file_hash = ?", (file_hash,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO raw_files (file_hash, file_type, original_name, stored_path, file_size, domain) VALUES (?, ?, ?, ?, ?, ?)",
                (file_hash, file_type, file_name, stored_path, file_size, domain)
            )
            count += 1
            new_files.append(file_name)

    conn.commit()
    conn.close()

    # Registra os logs com a conexão principal já fechada
    for file_name in new_files:
        log_event("INFO", "inbox_watcher", f"Arquivo ingestado: {file_name}")

    print(f"✅ [Jarvis Inbox] {count} novo(s) arquivo(s) processado(s) com sucesso!")

if __name__ == "__main__":
    process_inbox()