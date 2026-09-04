# -*- coding: utf-8 -*-
import time
import sqlite3
from pathlib import Path
from core.ingestion.ingestor import Ingestor
from core.storage.database import DB_PATH
from core.storage.logger import log_event

INBOX_DIR = Path("data/inbox")

def extract_on_fly(file_hash: str, stored_path: str):
    path = Path(stored_path)
    if not path.exists():
        return
    
    text = ""
    if path.suffix in ['.txt', '.md']:
        try:
            text = path.read_text(encoding="utf-8")
        except Exception as e:
            log_event("ERROR", "watcher_extractor", f"Erro ao ler {path.name}: {str(e)}")
            
    if text:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_content (
                file_hash TEXT PRIMARY KEY,
                extracted_text TEXT,
                FOREIGN KEY (file_hash) REFERENCES raw_files(file_hash)
            )
        ''')
        cursor.execute('''
            INSERT OR REPLACE INTO processed_content (file_hash, extracted_text)
            VALUES (?, ?)
        ''', (file_hash, text))
        conn.commit()
        conn.close()
        log_event("INFO", "watcher_extractor", f"Texto extraído automaticamente para o hash {file_hash[:12]}")

def watch_inbox():
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    ingestor = Ingestor()
    print(f"[Jarvis Watcher] Monitorando a pasta '{INBOX_DIR}'... (Pressione Ctrl+C para sair)")
    
    try:
        while True:
            files = [f for f in INBOX_DIR.iterdir() if f.is_file()]
            if files:
                print(f"\n[Jarvis Watcher] {len(files)} arquivo(s) detectado(s). Processando...")
                for file_path in files:
                    suffix = file_path.suffix.lower()
                    if suffix in ['.txt', '.md', '.pdf']:
                        f_type = "documents"
                    elif suffix in ['.jpg', '.png', '.jpeg']:
                        f_type = "images"
                    elif suffix in ['.mp3', '.wav', '.m4a']:
                        f_type = "audio"
                    else:
                        f_type = "documents"
                    
                    try:
                        file_hash = ingestor.ingest(str(file_path), f_type, domain="PERSONAL")
                        # Extrai o texto imediatamente após a ingestão
                        stored_dest = Path(f"data/{f_type}") / f"{file_hash}{suffix}"
                        extract_on_fly(file_hash, str(stored_dest))
                        
                        file_path.unlink()
                        print(f"Arquivo processado, indexado e removido da inbox: {file_path.name}")
                    except Exception as e:
                        print(f"Erro ao processar {file_path.name}: {e}")
            time.sleep(3)
    except KeyboardInterrupt:
        print("\n[Jarvis Watcher] Monitoramento encerrado pelo usuário.")

if __name__ == "__main__":
    watch_inbox()
