# -*- coding: utf-8 -*-
import sys
import argparse
from datetime import datetime
from core.storage.database import DB_PATH
from core.storage.logger import log_event
import sqlite3

def add_note(tag: str, content: str):
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO quick_notes (domain, tag, content, created_at)
        VALUES (?, ?, ?, ?)
    """, ("PERSONAL", tag.lower(), content, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    
    print(log_event("INFO", "notes_cli", f"Nota adicionada com sucesso [#{tag.lower()}]: {content}"))
    print(f"✅ [Jarvis] Nota registrada com sucesso na tag #{tag.lower()}!")

def add_habit(habit_name: str):
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO personal_habits (domain, habit, status, created_at)
        VALUES (?, ?, ?, ?)
    """, ("PERSONAL", habit_name, "PENDENTE", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    
    conn.commit()
    conn.close()
    
    print(log_event("INFO", "notes_cli", f"Hábito/Meta adicionado: {habit_name}"))
    print(f"🎯 [Jarvis] Hábito/Meta registrado com sucesso: '{habit_name}'!")

def main():
    parser = argparse.ArgumentParser(description="Jarvis Life OS - Captura Rápida de Notas e Hábitos")
    parser.add_argument("--tag", type=str, help="Tag da nota")
    parser.add_argument("--content", type=str, help="Conteúdo da nota rápida")
    parser.add_argument("--habit", type=str, help="Adicionar nova meta ou hábito pendente")

    args = parser.parse_args()

    if args.habit:
        add_habit(args.habit)
    elif args.tag and args.content:
        add_note(args.tag, args.content)
    else:
        print("⚠️ Uso incorreto. Exemplos:")
        print("  python -m modules.personal.notes_cli --tag estudos --content 'Estudar Python'")
        print("  python -m modules.personal.notes_cli --habit 'Correr no parque'")

if __name__ == "__main__":
    main()
