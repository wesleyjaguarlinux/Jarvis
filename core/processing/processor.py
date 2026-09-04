# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH
from core.storage.logger import log_event

class BaseProcessor:
    def __init__(self):
        pass

    def fetch_unprocessed_files(self):
        # Aqui podemos futuramente cruzar com uma tabela de processados
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT file_hash, file_type, stored_path, original_name FROM raw_files")
        files = cursor.fetchall()
        conn.close()
        return files

    def run(self):
        files = self.fetch_unprocessed_files()
        log_event("INFO", "processing", f"Iniciando varredura em {len(files)} arquivos no storage.")
        print(f"Total de arquivos na base para processamento: {len(files)}")
        for f in files:
            print(f" - [{f[1]}] {f[3]} (Hash: {f[0][:8]}...)")

if __name__ == "__main__":
    processor = BaseProcessor()
    processor.run()
