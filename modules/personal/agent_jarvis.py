# -*- coding: utf-8 -*-
import sqlite3
from core.storage.database import DB_PATH
from core.storage.logger import log_event

class JarvisAgent:
    def __init__(self):
        self.name = "Jarvis"

    def analyze_personal_context(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Estatísticas básicas da base de conhecimento pessoal
        cursor.execute("SELECT COUNT(*) FROM raw_files")
        total_files = cursor.fetchone()[0]
        
        cursor.execute("SELECT file_type, COUNT(*) FROM raw_files GROUP BY file_type")
        types_summary = cursor.fetchall()
        
        conn.close()
        
        log_event("INFO", "agent", "Análise de contexto pessoal executada com sucesso.")
        
        print(f"[{self.name} - Conselheiro Operacional]")
        print(f"Status do Segundo Cérebro: {total_files} itens ingeridos no total.")
        print("Distribuição por Categoria:")
        for t_type, count in types_summary:
            print(f"  - {t_type}: {count} arquivo(s)")

if __name__ == "__main__":
    agent = JarvisAgent()
    agent.analyze_personal_context()
