# -*- coding: utf-8 -*-
import hashlib
import shutil
from pathlib import Path
import sqlite3

from core.storage.database import DB_PATH, init_db
from core.storage.logger import log_event

class Ingestor:
    def __init__(self):
        init_db() # Garante que o banco e as tabelas sempre existam
        self.type_dirs = {
            "audio": Path("data/audio"),
            "images": Path("data/images"),
            "documents": Path("data/documents")
        }

    def _calculate_sha256(self, file_path: Path) -> str:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def ingest(self, file_path: str, file_type: str, domain: str = "PERSONAL") -> str:
        src_path = Path(file_path)
        if not src_path.exists():
            msg = f"Arquivo nao encontrado: {src_path}"
            log_event("ERROR", "ingestion", msg)
            raise FileNotFoundError(msg)

        if file_type not in self.type_dirs:
            msg = f"Tipo de arquivo invalido: {file_type}"
            log_event("ERROR", "ingestion", msg)
            raise ValueError(msg)

        file_hash = self._calculate_sha256(src_path)
        dest_dir = self.type_dirs[file_type]
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = src_path.suffix
        dest_path = dest_dir / f"{file_hash}{file_extension}"

        if not dest_path.exists():
            shutil.copy2(src_path, dest_path)
            log_event("INFO", "ingestion", f"Arquivo copiado para {dest_path}")
        else:
            log_event("INFO", "ingestion", f"Deduplicação acionada para o hash {file_hash[:12]}")

        file_size = src_path.stat().st_size

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO raw_files (file_hash, file_type, original_name, stored_path, file_size, domain)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (file_hash, file_type, src_path.name, str(dest_path), file_size, domain.upper()))
            conn.commit()
            log_event("INFO", "ingestion", f"Metadados salvos no SQLite ({domain}) para: {src_path.name}")
        except Exception as e:
            log_event("ERROR", "ingestion", f"Erro ao salvar no banco: {str(e)}")
            raise
        finally:
            conn.close()

        print(f"Sucesso [{domain}]! Inserido: {src_path.name} -> Hash: {file_hash[:12]}...")
        return file_hash

if __name__ == "__main__":
    print("Ingestor atualizado com auto-init do DB.")
