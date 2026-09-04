# -*- coding: utf-8 -*-
import time
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH
from core.storage.logger import log_event

INBOX_DIR = Path("data/inbox")
PROCESSED_DIR = Path("data/processed")

def setup_folders():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

def process_inbox_files():
    setup_folders()
    
    if not DB_PATH.exists():
        print("[Jarvis Watcher] Banco de dados não encontrado.")
        return

    files = list(INBOX_DIR.glob("*.*"))
    if not files:
        print("📂 [Jarvis Watcher] Inbox vazia. Nenhum arquivo novo para processar.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for file_path in files:
        if file_path.suffix.lower() in ['.txt', '.md']:
            try:
                content = file_path.read_text(encoding="utf-8")
                
                # Registra na tabela raw_files com domínio PERSONAL
                cursor.execute("""
                    INSERT INTO raw_files (domain, file_name, file_path, content_summary, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, ("PERSONAL", file_path.name, str(file_path), content[:200])) # Salva um resumo dos primeiros caracteres
                
                conn.commit()
                log_event("INFO", "inbox_watcher", f"Arquivo processado e indexado: {file_path.name}")
                print(f"✅ [Jarvis Watcher] Arquivo importado com sucesso: {file_path.name}")
                
                # Move o arquivo processado para a pasta de backup/organização
                dest_path = PROCESSED_DIR / file_path.name
                file_path.rename(dest_path)
                
            except Exception as e:
                print(f"❌ Erro ao processar {file_path.name}: {e}")
                log_event("ERROR", "inbox_watcher", f"Erro ao processar {file_path.name}: {str(e)}")

    conn.close()

if __name__ == "__main__":
    print("👀 [Jarvis] Varredura da Inbox iniciada...")
    process_inbox_files()