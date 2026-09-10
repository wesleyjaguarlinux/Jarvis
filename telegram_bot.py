# -*- coding: utf-8 -*-
import logging
import sqlite3
import os
from pathlib import Path
import shutil
from datetime import datetime, date, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.db.sqlite import SqliteDb
from agno.tools.python import PythonTools
import yt_dlp
from openai import OpenAI
from bs4 import BeautifulSoup
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from core.storage.database import DB_PATH

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TELEGRAM_TOKEN = "8912660577:AAG6Kv4sFGkuTfRWvgt-ka3Q01QyYYyvbhg"

DOWNLOAD_DIR = Path.home() / "Downloads" / "Jarvis_Downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
USER_DOWNLOADS = Path.home() / "Downloads"
USER_DOCUMENTS = Path.home() / "Documents"

EXACT_PROFILE_PATH = Path(r"C:\Users\Wesley\Downloads\Cérebro-20260402T184614Z-1-001\Cérebro\Contexto_Jarvis\Perfil_Mestre.md")
EXACT_AGENDA_PATH = Path(r"C:\Users\Wesley\Downloads\Cérebro-20260402T184614Z-1-001\Cérebro\Contexto_Jarvis\Agenda_Semanal.md")
EXACT_REGISTRO_PATH = Path(r"C:\Users\Wesley\Downloads\Cérebro-20260402T184614Z-1-001\Cérebro\Contexto_Jarvis\Registro_Diario.md")

client = OpenAI()
AGENT_DB_PATH = Path.cwd() / "core" / "storage" / "agent_memory.db"
AGENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

PENDING_APPROVALS = {}
GLOBAL_BOT_APP = None

def init_optimized_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            content TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS deadlines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_description TEXT,
            due_date DATE,
            status TEXT DEFAULT 'pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS domestic_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_name TEXT,
            category TEXT, 
            due_date DATE,
            due_time TEXT,
            status TEXT DEFAULT 'pendente',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS price_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            url TEXT,
            target_price REAL,
            last_checked_price REAL,
            status TEXT DEFAULT 'monitorando',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_blocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            block_date DATE,
            start_time TEXT,
            end_time TEXT,
            activity_category TEXT,
            description TEXT,
            interruptions TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_optimized_db()

# ---------------------------------------------------------------------------
# MOTOR DE BLOCOS DE TEMPO E COMPILADOR DIÁRIO (BACKEND)
# ---------------------------------------------------------------------------

def backend_add_time_block(start_time: str, end_time: str, activity_category: str, description: str, interruptions: str = "Nenhuma") -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today_str = date.today().strftime("%Y-%m-%d")
    cursor.execute("""
        INSERT INTO time_blocks (block_date, start_time, end_time, activity_category, description, interruptions) 
        VALUES (?, ?, ?, ?, ?, ?)
    """, (today_str, start_time, end_time, activity_category, description, interruptions))
    conn.commit()
    conn.close()
    return f"⏱️ Bloco registrado [{start_time} - {end_time}] ({activity_category.upper()}): {description} | Distrações: {interruptions}"

def backend_compile_daily_summary() -> str:
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    today_str = date.today().strftime("%Y-%m-%d")
    cursor.execute("""
        SELECT start_time, end_time, activity_category, description, interruptions 
        FROM time_blocks 
        WHERE block_date = ? 
        ORDER BY start_time ASC
    """, (today_str,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return f"⚠️ Nenhum bloco de tempo registrado para hoje ({today_str}). Envie seus blocos ao longo do dia para compilar o resumo."
        
    summary = f"# 📝 REGISTRO DIÁRIO DE EXECUÇÃO — [{today_str}]\n\n"
    summary += "## ⏱️ 1. Linha do Tempo e Blocos de Produção\n"
    for st, et, cat, desc, intr in rows:
        summary += f"- **[{st} - {et}] ({cat.upper()}):** {desc} | *Gargalo/Interrupção:* {intr}\n"
        
    summary += "\n## 🎯 2. Análise de Foco e Próximos Passos\n"
    summary += "- **Balanço:** Blocos computados e estruturados com sucesso para exportação ao Obsidian.\n"
    summary += "- **Ação Corretiva:** Manter rastreio contínuo e eliminar distrações mapeadas nos intervalos.\n"
    
    return summary

def backend_add_domestic_task(task_name: str, category: str, due_date: str, due_time: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_name FROM domestic_tasks WHERE due_date = ? AND due_time = ? AND status = 'pendente'", (due_date, due_time))
    conflict = cursor.fetchone()
    
    if conflict:
        conn.close()
        return f"🚨 CONFLITO DE AGENDA DETECTADO!\n\nVocê já tem o compromisso '[ID {conflict[0]}] {conflict[1]}' agendado para o dia {due_date} às {due_time}."

    cursor.execute("INSERT INTO domestic_tasks (task_name, category, due_date, due_time) VALUES (?, ?, ?, ?)", 
                   (task_name, category, due_date, due_time))
    conn.commit()
    conn.close()
    return f"🏠 Compromisso registrado [{category}]: '{task_name}' para {due_date} às {due_time}."

def backend_list_domestic_tasks() -> str:
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_name, category, due_date, due_time, status FROM domestic_tasks ORDER BY due_date ASC, due_time ASC")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhuma tarefa cadastrada."
    msg = "🏠 Operação Doméstica e Rotina:\n"
    for tid, name, cat, ddate, dtime, status in rows:
        t_str = f"às {dtime}" if dtime else ""
        msg += f"[ID {tid}] ({cat.upper()}) {ddate} {t_str} — {name} [{status}]\n"
    return msg

# ---------------------------------------------------------------------------
# FERRAMENTAS DO VAULT
# ---------------------------------------------------------------------------

def add_time_block(start_time: str, end_time: str, activity_category: str, description: str, interruptions: str = "Nenhuma") -> str:
    """Registra um bloco de tempo estruturado com horários, categoria, o que foi feito e interrupções."""
    return backend_add_time_block(start_time, end_time, activity_category, description, interruptions)

def compile_daily_summary() -> str:
    """Compila todos os blocos do dia em um relatório pronto para o Obsidian."""
    return backend_compile_daily_summary()

def add_domestic_task(task_name: str, category: str, due_date: str, due_time: str) -> str:
    return backend_add_domestic_task(task_name, category, due_date, due_time)

def list_domestic_tasks() -> str:
    return backend_list_domestic_tasks()

def read_obsidian_master_profile() -> str:
    output = ""
    if EXACT_PROFILE_PATH.exists():
        try:
            with open(EXACT_PROFILE_PATH, "r", encoding="utf-8") as f:
                output += f"📂 [PERFIL MESTRE]:\n{f.read()}\n\n"
        except Exception: pass
            
    if EXACT_AGENDA_PATH.exists():
        try:
            with open(EXACT_AGENDA_PATH, "r", encoding="utf-8") as f:
                output += f"📅 [AGENDA SEMANAL]:\n{f.read()}\n\n"
        except Exception: pass

    if EXACT_REGISTRO_PATH.exists():
        try:
            with open(EXACT_REGISTRO_PATH, "r", encoding="utf-8") as f:
                output += f"📝 [REGISTRO DIÁRIO]:\n{f.read()}\n"
        except Exception: pass
            
    return output if output else "❌ Nenhuma nota encontrada."

def sync_obsidian_notes() -> str:
    return read_obsidian_master_profile()

def search_obsidian_knowledge(query_term: str = "") -> str:
    return read_obsidian_master_profile()

# ---------------------------------------------------------------------------
# SUBAGENTES E EQUIPE
# ---------------------------------------------------------------------------
media_agent = Agent(
    name="Silas",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[lambda: "Ok"],
    instructions=["Mídias."]
)

database_agent = Agent(
    name="Vault",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[add_time_block, compile_daily_summary, add_domestic_task, list_domestic_tasks, sync_obsidian_notes, search_obsidian_knowledge],
    instructions=[
        "Especialista em SQLite, blocos de tempo, compilação diária e cofre do Obsidian.",
        "DATA ATUAL: 2026-09-10. Utilize add_time_block() para registrar blocos e compile_daily_summary() para gerar o resumo do dia."
    ]
)

hunter_agent = Agent(
    name="Hunter",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[lambda: "Ok"],
    instructions=["Prospecção."]
)

coder_agent = Agent(
    name="Coder",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[lambda: "Ok"],
    instructions=["Técnico."]
)

jarvis_team = Team(
    name="JarvisTeam",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[media_agent, database_agent, hunter_agent, coder_agent],
    db=SqliteDb(db_file=str(AGENT_DB_PATH)),
    add_history_to_context=True,
    num_history_runs=5,
    instructions=[
        "Você é o Jarvis, assistente pessoal autônomo de Wesley Cruz.",
        "--- POSTURA ---",
        "Conselheiro analítico sênior: exija rigor e aponte gargalos."
    ],
    markdown=True
)

async def trigger_daily_compilation_reminder():
    global GLOBAL_BOT_APP
    if not GLOBAL_BOT_APP: return
    try:
        conn_db = sqlite3.connect(AGENT_DB_PATH)
        cur_db = conn_db.cursor()
        cur_db.execute("SELECT DISTINCT session_id FROM agent_sessions LIMIT 1")
        row_chat = cur_db.fetchone()
        conn_db.close()
        if row_chat:
            summary = backend_compile_daily_summary()
            await GLOBAL_BOT_APP.bot.send_message(
                chat_id=int(row_chat[0]), 
                text=f"⏰ *Fechamento do Dia - Relatório Pronto para o Obsidian:*\n\n{summary}", 
                parse_mode="Markdown"
            )
    except Exception as e:
        logging.error(f"Erro no lembrete de compilação: {str(e)}")

async def process_user_input(update: Update, text_content: str):
    user_id = str(update.effective_user.id)
    text_lower = text_content.lower().strip()

    if "resumo" in text_lower or "compilar" in text_lower or "relatório" in text_lower or "produção" in text_lower:
        await update.message.chat.send_action("typing")
        res = backend_compile_daily_summary()
        await update.message.reply_text(res, parse_mode="Markdown")
        return

    await update.message.chat.send_action("typing")
    try:
        response = jarvis_team.run(text_content, session_id=user_id)
        reply_text = response.content if response and response.content else "Pronto, chefe."
        try:
            await update.message.reply_text(reply_text, parse_mode="Markdown")
        except Exception:
            await update.message.reply_text(reply_text)
    except Exception as e:
        await update.message.reply_text(f"❌ Erro crítico: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await process_user_input(update, update.message.text.strip())

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.chat.send_action("record_audio")
    try:
        voice_file = await context.bot.get_file(update.message.voice.file_id)
        audio_path = DOWNLOAD_DIR / f"voice_{update.message.voice.file_unique_id}.oga"
        await voice_file.download_to_drive(audio_path)
        with open(audio_path, "rb") as f:
            transcript = client.audio.transcriptions.create(model="whisper-1", file=f, language="pt")
        await update.message.reply_text(f"🎙️ _{transcript.text}_", parse_mode="Markdown")
        if audio_path.exists(): os.remove(audio_path)
        await process_user_input(update, transcript.text)
    except Exception as e:
        await update.message.reply_text(f"❌ Erro no áudio: {str(e)}")

def main():
    global GLOBAL_BOT_APP
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    GLOBAL_BOT_APP = app

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.COMMAND, handle_message))

    scheduler = BackgroundScheduler()
    # Dispara o resumo de fechamento às 21:00h
    scheduler.add_job(trigger_daily_compilation_reminder, 'cron', hour=21, minute=0)
    scheduler.start()

    print("🤖 Jarvis Team (Blocos de Tempo e Compilador Ativo) Pronto...")
    app.run_polling()

if __name__ == '__main__':
    main()
