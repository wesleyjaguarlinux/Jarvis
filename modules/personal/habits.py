# -*- coding: utf-8 -*-
import sqlite3
import sys
from pathlib import Path
from core.storage.database import DB_PATH, init_db
from core.storage.logger import log_event

def init_habits_table():
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS personal_habits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            habit_name TEXT NOT NULL,
            status TEXT DEFAULT 'PENDENTE',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

class HabitsManager:
    def __init__(self):
        init_habits_table()

    def add_habit(self, name: str):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO personal_habits (habit_name, status) VALUES (?, 'PENDENTE')", (name,))
        conn.commit()
        conn.close()
        log_event("INFO", "habits_manager", f"Hábito/Meta adicionado: {name}")
        print(f"[Jarvis Habits] Meta registrada: '{name}'")

    def list_habits(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, habit_name, status, created_at FROM personal_habits ORDER BY created_at DESC")
        habits = cursor.fetchall()
        conn.close()

        print("\n[Jarvis Habits - Suas Metas e Hábitos]")
        if not habits:
            print("Nenhuma meta registrada.")
            return
        for h in habits:
            print(f"  [{h[0]}] {h[2]} - {h[1]} (Criado em: {h[3]})")

if __name__ == "__main__":
    manager = HabitsManager()
    if len(sys.argv) > 1:
        habit_text = " ".join(sys.argv[1:])
        manager.add_habit(habit_text)
    else:
        manager.list_habits()
