# -*- coding: utf-8 -*-
import sys
import argparse
import urllib.request
import re
import sqlite3
from core.storage.database import DB_PATH
from core.storage.logger import log_event

def fetch_and_save_url(url: str, tag: str = "web"):
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados não encontrado.")
        return

    print(f"🌐 [Jarvis Web] Baixando conteúdo de: {url}...")
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        )
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8', errors='ignore')
        
        # Extrai o título da página de forma simples
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else url

        # Limpa tags HTML básicas para guardar o texto resumido
        clean_text = re.sub(r'<[^>]+>', '', html)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()[:300] # Pega um resumo dos primeiros 300 caracteres

        content = f"[{title}] - {url} | Resumo: {clean_text}"

        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quick_notes (tag, content) VALUES (?, ?)", (tag, content))
        conn.commit()
        conn.close()

        log_event("INFO", "web_fetcher", f"URL capturada: {url}")
        print(f"✅ [Jarvis Web] Conteúdo capturado e salvo nas notas rápidas com a tag #{tag}!")

    except Exception as e:
        print(f"❌ [Jarvis Web] Erro ao acessar a URL: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        fetch_and_save_url(sys.argv[1])
    else:
        print("⚠️ Uso: python -m modules.personal.web_fetcher <URL>")