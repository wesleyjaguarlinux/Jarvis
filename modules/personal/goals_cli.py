# -*- coding: utf-8 -*-
import sys
import argparse
import sqlite3
from datetime import datetime
from core.storage.database import DB_PATH
from core.storage.logger import log_event

def init_goals_table():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS daily_goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_date TEXT,
            objective TEXT,
            status TEXT DEFAULT 'PENDENTE'
        )
    ''')
    conn.commit()
    conn.close()

def add_goal(objective: str):
    init_goals_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO daily_goals (goal_date, objective) VALUES (?, ?)", (today, objective))
    conn.commit()
    conn.close()
    print(f"🎯 [Jarvis Goals] Meta adicionada para hoje: '{objective}'")

def list_today_goals():
    init_goals_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("SELECT id, objective, status FROM daily_goals WHERE goal_date = ?", (today,))
    goals = cursor.fetchall()
    conn.close()

    print(f"\n🎯 [Metas do Dia - {today}]")
    if goals:
        for gid, obj, status in goals:
            icon = "✅" if status == "CONCLUIDO" else "⏳"
            print(f"  {icon} [{gid}] {obj} ({status})")
    else:
        print("  (Nenhuma meta definida para hoje. Defina uma com 'python main.py goals --add <texto>')")
    print()

def complete_goal(goal_id: int):
    init_goals_table()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE daily_goals SET status = 'CONCLUIDO' WHERE id = ?", (goal_id,))
    conn.commit()
    conn.close()
    print(f"✅ [Jarvis Goals] Meta #{goal_id} marcada como CONCLUIDA!")

if __name__ == "__main__":
    pass