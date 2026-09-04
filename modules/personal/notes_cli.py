# -*- coding: utf-8 -*-
import sys
import argparse
import sqlite3
from core.storage.database import DB_PATH
from core.storage.logger import log_event

def add_note(tag: str, content: str):
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados nao encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quick_notes (tag, content) VALUES (?, ?)", (tag, content))
    conn.commit()
    conn.close()

    log_event("INFO", "notes_cli", f"Nota adicionada com tag #{tag}")
    print(f"✅ [Jarvis] Nota registrada com sucesso na tag #{tag}!")

def list_notes():
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados nao encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, tag, content, created_at FROM quick_notes ORDER BY created_at DESC")
    notes = cursor.fetchall()
    conn.close()

    if not notes:
        print("📝 [Jarvis] Nenhuma nota registrada no momento!")
        return

    print("\n📝 [Notas Rapidas Registradas]")
    for note_id, tag, content, created_at in notes:
        print(f"  [{note_id}] #{tag} - {content} ({created_at})")
    print()

def main():
    parser = argparse.ArgumentParser(description="Jarvis Life OS - Gerenciamento de Notas Rapidas")
    parser.add_argument("--add", nargs=2, metavar=('TAG', 'CONTEUDO'), help="Adiciona uma nova nota (ex: --add estudos 'Aprender SQLite')")
    parser.add_argument("--list", action="store_true", help="Lista todas as notas cadastradas")

    args = parser.parse_args()

    if args.add:
        tag, content = args.add
        add_note(tag, content)
    elif args.list:
        list_notes()
    else:
        print("⚠️ Uso incorreto. Exemplos:")
        print("  python -m modules.personal.notes_cli --add tag 'conteudo'")
        print("  python -m modules.personal.notes_cli --list")

if __name__ == "__main__":
    main()