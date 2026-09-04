# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
from core.storage.database import DB_PATH
from core.storage.logger import log_event
from core.processing.finance_parser import FinanceParser

class TextExtractor:
    def __init__(self):
        self.finance_parser = FinanceParser()

    def extract_content(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processed_content (
                file_hash TEXT PRIMARY KEY,
                extracted_text TEXT,
                FOREIGN KEY (file_hash) REFERENCES raw_files(file_hash)
            )
        ''')
        
        cursor.execute("SELECT file_hash, file_type, stored_path FROM raw_files")
        files = cursor.fetchall()
        conn.close()

        for file_hash, file_type, stored_path in files:
            path = Path(stored_path)
            if not path.exists():
                continue
                
            text = ""
            if file_type == "documents" and path.suffix == ".txt":
                try:
                    text = path.read_text(encoding="utf-8")
                except Exception as e:
                    log_event("ERROR", "extractor", f"Erro ao ler {path.name}: {str(e)}")
            
            if text:
                c_conn = sqlite3.connect(DB_PATH)
                c_cursor = c_conn.cursor()
                try:
                    c_cursor.execute('''
                        INSERT OR REPLACE INTO processed_content (file_hash, extracted_text)
                        VALUES (?, ?)
                    ''', (file_hash, text))
                    c_conn.commit()
                    log_event("INFO", "extractor", f"Texto extraído para o hash {file_hash[:12]}")
                    print(f"Extraído texto do arquivo: {path.name}")
                    
                    # Aciona o parser financeiro caso o conteúdo contenha termos de extrato/financeiro
                    if "extrato" in text.lower() or "financeiro" in text.lower():
                        self.finance_parser.parse_simulated_extrato(file_hash, text)

                finally:
                    c_conn.close()

if __name__ == "__main__":
    extractor = TextExtractor()
    extractor.extract_content()
    print("Pipeline de extração e parsing financeiro concluído!")
