# -*- coding: utf-8 -*-
import logging
import sqlite3
import os
from pathlib import Path
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from agno.agent import Agent
from agno.models.openai import OpenAIChat
import yt_dlp
from core.storage.database import DB_PATH

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
TELEGRAM_TOKEN = "8912660577:AAG6Kv4sFGkuTfRWvgt-ka3Q01QyYYyvbhg"

DOWNLOAD_DIR = Path.home() / "Downloads" / "Jarvis_Downloads"
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)

def add_quick_note(content: str, tag: str = "telegram") -> str:
    """Adiciona uma nota rápida ao banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quick_notes (tag, content) VALUES (?, ?)", (tag, content))
    conn.commit()
    conn.close()
    return f"Nota salva com sucesso: '{content}'"

def add_daily_goal(goal_text: str) -> str:
    """Adiciona uma nova meta ou tarefa diária ao banco de dados."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(daily_goals)")
    cols = [col[1] for col in cursor.fetchall()]
    col_name = 'goal' if 'goal' in cols else ('task' if 'task' in cols else cols[1])
    
    if 'status' in cols:
        cursor.execute(f"INSERT INTO daily_goals ({col_name}, status) VALUES (?, 'ativo')", (goal_text,))
    else:
        cursor.execute(f"INSERT INTO daily_goals ({col_name}) VALUES (?)", (goal_text,))
    conn.commit()
    conn.close()
    return f"Meta cadastrada com sucesso: '{goal_text}'"

def list_all_notes() -> str:
    """Lista todas as notas rápidas registradas no banco de dados com seus IDs."""
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, tag, content, created_at FROM quick_notes ORDER BY id DESC")
    notes = cursor.fetchall()
    conn.close()
    if not notes: return "Nenhuma nota encontrada."
    
    msg = "🧠 Notas Registradas:\n"
    for nid, tag, content, created_at in notes:
        msg += f"[ID {nid}] [{tag}] {content} ({created_at})\n"
    return msg

def list_all_goals() -> str:
    """Lista todas as metas e tarefas diárias cadastradas com seus IDs e status."""
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(daily_goals)")
    cols = [col[1] for col in cursor.fetchall()]
    col_name = 'goal' if 'goal' in cols else ('task' if 'task' in cols else cols[1])
    
    cursor.execute(f"SELECT id, {col_name}, status FROM daily_goals ORDER BY id DESC")
    goals = cursor.fetchall()
    conn.close()
    if not goals: return "Nenhuma meta cadastrada."
    
    msg = "🎯 Metas do Dia:\n"
    for gid, gtext, gstatus in goals:
        msg += f"[ID {gid}] {gtext} — [{gstatus}]\n"
    return msg

def delete_item_by_id(item_type: str, item_id: int) -> str:
    """Exclui uma nota ou uma meta do banco de dados com base no ID numérico.
    Args:
        item_type: Deve ser 'nota' ou 'meta'.
        item_id: O número do ID do registro.
    """
    table = "daily_goals" if item_type.lower() == "meta" else "quick_notes"
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"DELETE FROM {table} WHERE id = ?", (item_id,))
    rc = cursor.rowcount
    conn.commit()
    conn.close()
    
    if rc > 0:
        return f"🗑️ {item_type.capitalize()} ID {item_id} excluída com sucesso!"
    return f"⚠️ Nenhum registro encontrado com o ID {item_id} em {item_type}s."

def download_media_from_url(url: str) -> str:
    """Baixa um vídeo ou áudio da internet (YouTube, Instagram, TikTok, etc) diretamente para o computador local.
    Args:
        url: O link completo da URL enviada pelo usuário.
    """
    ydl_opts = {
        'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'),
        'format': 'best',
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get('title', 'Vídeo baixado')
            return f"📥 Mídia baixada com sucesso para a pasta local do Jarvis!\n📁 Título: {title}"
    except Exception as e:
        return f"❌ Falha ao baixar a mídia: {str(e)}"

jarvis_agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[add_quick_note, add_daily_goal, list_all_notes, list_all_goals, delete_item_by_id, download_media_from_url],
    instructions=[
        "Você é o Jarvis, um assistente pessoal autônomo conectado ao computador local do usuário.",
        "Você gerencia notas, metas e também é capaz de baixar vídeos e mídias da internet (YouTube, Instagram, etc) usando ferramentas locais.",
        "Interprete os pedidos do usuário em linguagem natural e acione a ferramenta correta.",
        "Responda de forma direta e objetiva em português do Brasil."
    ],
    markdown=True
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    await update.message.chat.send_action("typing")

    try:
        response = jarvis_agent.run(text)
        reply_text = response.content if response and response.content else "Comando processado, chefe."
        await update.message.reply_text(reply_text, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Erro crítico no Agente Jarvis: {str(e)}")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.COMMAND, handle_message))
    print("🤖 Jarvis Agent (Nível 2: Download Anti-403) Ativo...")
    app.run_polling()

if __name__ == '__main__':
    main()
