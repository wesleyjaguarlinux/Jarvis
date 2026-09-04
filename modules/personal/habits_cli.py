# -*- coding: utf-8 -*-
import sys
import argparse
import sqlite3
from core.storage.database import DB_PATH
from core.storage.logger import log_event

def list_pending_habits():
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados nao encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, habit_name, created_at FROM personal_habits WHERE status = 'PENDENTE'")
    habits = cursor.fetchall()
    conn.close()

    if not habits:
        print("🎯 [Jarvis] Nenhum habito pendente no momento!")
        return

    print("\n🎯 [Habitos e Metas Pendentes]")
    for habit_id, habit_text, created_at in habits:
        print(f"  [{habit_id}] {habit_text} (Criado em: {created_at})")
    print()

def complete_habit(habit_id: int):
    if not DB_PATH.exists():
        print("[Jarvis CLI] Banco de dados nao encontrado.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT habit_name FROM personal_habits WHERE id = ?", (habit_id,))
    row = cursor.fetchone()
    
    if not row:
        print(f"⚠️ [Jarvis] Habito com ID {habit_id} não encontrado.")
        conn.close()
        return

    habit_name = row[0]
    cursor.execute("UPDATE personal_habits SET status = 'CONCLUIDO' WHERE id = ?", (habit_id,))
    conn.commit()
    conn.close()
    
    log_event("INFO", "habits_cli", f"Habito concluido: {habit_name} (ID: {habit_id})")
    print(f"✅ [Jarvis] Habito/Meta ID {habit_id} ('{habit_name}') marcado como CONCLUÍDO com sucesso!")

def main():
    parser = argparse.ArgumentParser(description="Jarvis Life OS - Gerenciamento de Habitos e Metas")
    parser.add_argument("--list", action="store_true", help="Lista todos os habitos pendentes")
    parser.add_argument("--done", type=int, help="Marca um habito como CONCLUIDO pelo ID")

    args = parser.parse_args()

    if args.list:
        list_pending_habits()
    elif args.done is not None:
        complete_habit(args.done)
    else:
        print("⚠️ Uso incorreto. Exemplos:")
        print("  python -m modules.personal.habits_cli --list")
        print("  python -m modules.personal.habits_cli --done 1")

if __name__ == "__main__":
    main()