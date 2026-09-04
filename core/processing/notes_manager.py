# -*- coding: utf-8 -*-
import sqlite3
import sys
from core.storage.database import DB_PATH
from core.storage.logger import log_event

class NotesManager:
    def __init__(self):
        pass

    def add_note(self, content: str, tag: str = "geral"):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO quick_notes (content, tag) VALUES (?, ?)", (content, tag.lower()))
        conn.commit()
        conn.close()
        log_event("INFO", "notes_manager", f"Nota rápida adicionada com tag [{tag}].")
        print(f"[Jarvis Notes] Nota salva [{tag}]: '{content}'")

    def list_notes(self, filter_tag: str = None):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if filter_tag:
            cursor.execute("SELECT id, content, tag, created_at FROM quick_notes WHERE tag = ? ORDER BY created_at DESC", (filter_tag.lower(),))
            print(f"\n[Jarvis Notes - Filtrado por tag: '{filter_tag}']")
        else:
            cursor.execute("SELECT id, content, tag, created_at FROM quick_notes ORDER BY created_at DESC")
            print("\n[Jarvis Notes - Suas Notas Rápidas]")
            
        notes = cursor.fetchall()
        conn.close()

        if not notes:
            print("Nenhuma nota encontrada.")
            return
        for n in notes:
            print(f"  [{n[0]}] ({n[2].upper()}) - {n[1]}  ({n[3]})")

if __name__ == "__main__":
    manager = NotesManager()
    args = sys.argv[1:]
    
    if not args:
        manager.list_notes()
    else:
        # Verifica se passou uma tag no formato --tag nome
        tag = "geral"
        content_args = []
        
        i = 0
        while i < len(args):
            if args[i] == "--tag" and i + 1 < len(args):
                tag = args[i + 1]
                i += 2
            else:
                content_args.append(args[i])
                i += 1
                
        if content_args:
            text = " ".join(content_args)
            manager.add_note(text, tag)
        else:
            # Se chamou apenas com uma tag para filtro (ex: python -m notes_manager --tag estudos)
            manager.list_notes(filter_tag=tag if tag != "geral" else None)
