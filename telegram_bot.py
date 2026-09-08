# -*- coding: utf-8 -*-
import logging
sqlite3 = __import__('sqlite3')
import os
from pathlib import Path
import shutil
from datetime import datetime, date
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

client = OpenAI()
AGENT_DB_PATH = Path.cwd() / "core" / "storage" / "agent_memory.db"
AGENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

PENDING_APPROVALS = {}
GLOBAL_BOT_APP = None

# ---------------------------------------------------------------------------
# INICIALIZAÇÃO DE TABELAS (PERFIL, DEADLINES, PREÇOS E URLS ALVO)
# ---------------------------------------------------------------------------
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
        CREATE TABLE IF NOT EXISTS price_tracker (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            url TEXT,
            price REAL,
            checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitored_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_optimized_db()

# ---------------------------------------------------------------------------
# FERRAMENTAS DO VAULT (MEMÓRIA CIRÚRGICA E PERFIL)
# ---------------------------------------------------------------------------

def add_quick_note(content: str, tag: str = "telegram") -> str:
    """Adiciona uma nota rápida ao banco de dados SQLite."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO quick_notes (tag, content) VALUES (?, ?)", (tag, content))
    conn.commit()
    conn.close()
    return f"Nota salva com sucesso: '{content}'"

def add_deadline(task_description: str, due_date: str) -> str:
    """Adiciona um compromisso ou prazo específico."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO deadlines (task_description, due_date) VALUES (?, ?)", (task_description, due_date))
    conn.commit()
    conn.close()
    return f"📅 Prazo registrado: '{task_description}' para {due_date}."

def list_all_deadlines() -> str:
    """Lista todos os prazos e compromissos cadastrados."""
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, task_description, due_date, status FROM deadlines ORDER BY due_date ASC")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhum prazo cadastrado."
    
    msg = "📅 Prazos e Compromissos:\n"
    for did, desc, ddate, status in rows:
        msg += f"[ID {did}] {ddate} — {desc} [{status}]\n"
    return msg

def update_user_profile(category: str, content: str) -> str:
    """Atualiza um aspecto do perfil de longo prazo do usuário (como CEP ou localização)."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_profile (category, content) VALUES (?, ?)", (category, content))
    conn.commit()
    conn.close()
    return f"🧬 Perfil atualizado [{category}]: {content}"

def read_user_profile() -> str:
    """Lê todo o perfil cognitivo e de localização de longo prazo acumulado sobre o usuário."""
    if not DB_PATH.exists(): return "Perfil não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT category, content, updated_at FROM user_profile ORDER BY id DESC LIMIT 30")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhum perfil comportamental registrado ainda."
    
    msg = "🧠 Perfil Cognitivo e Logístico:\n"
    for cat, content, dt in rows:
        msg += f"- [{cat}] {content} ({dt})\n"
    return msg

# ---------------------------------------------------------------------------
# FERRAMENTAS DO SILAS (MÍDIA, WEB, SCRAPING E LOGÍSTICA)
# ---------------------------------------------------------------------------

def add_monitored_url(item_name: str, url: str) -> str:
    """Cadastra um link de insumo (brigadeiros, carnes, frutas) para monitoramento automático."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO monitored_urls (item_name, url) VALUES (?, ?)", (item_name, url))
    conn.commit()
    conn.close()
    return f"🎯 Insumo '{item_name}' cadastrado para monitoramento logístico!"

def list_monitored_urls() -> str:
    """Lista todos os produtos cadastrados para monitoramento de preços."""
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, url FROM monitored_urls")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhum link cadastrado."
    
    msg = "📋 Insumos Monitorados:\n"
    for uid, name, u in rows:
        msg += f"[ID {uid}] {name}\n  Link: {u}\n"
    return msg

def analyze_web_content(url: str) -> str:
    """Extrai conteúdo de um link web."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        return f"🌐 Conteúdo extraído ({url}):\n\n{'\n'.join(chunk for chunk in chunks if chunk)[:4000]}"
    except Exception as e:
        return f"❌ Erro ao extrair link {url}: {str(e)}"

def check_item_price(item_name: str, url: str) -> str:
    """Verifica preço de um item e registra no SQLite considerando análise de viabilidade."""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO price_tracker (item_name, url, price) VALUES (?, ?, ?)", (item_name, url, 0.0))
        conn.commit()
        conn.close()
        
        return f"🌐 Varredura realizada para '{item_name}'. O Silas avaliará o impacto do frete/distância com base na sua região cadastrada."
    except Exception as e:
        return f"❌ Erro ao monitorar preço de {item_name}: {str(e)}"

def list_tracked_prices() -> str:
    """Lista histórico de preços."""
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, price, url, checked_at FROM price_tracker ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhum preço registrado."
    
    msg = "💰 Histórico de Preços e Viabilidade:\n"
    for name, prc, u, dt in rows:
        msg += f"- {name}: R$ {prc} ({dt})\n  Link: {u}\n"
    return msg

def download_media_from_url(url: str) -> str:
    """Baixa mídia da internet."""
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
            return f"📥 Mídia baixada com sucesso! Título: {info.get('title', 'Vídeo')}"
    except Exception as e:
        return f"❌ Falha ao baixar: {str(e)}"

def organize_downloads_folder() -> str:
    """Organiza a pasta Downloads."""
    if not USER_DOWNLOADS.exists(): return "Pasta de Downloads não encontrada."
    extensions = {
        'Videos_Edicao': ['.mp4', '.mkv', '.avi', '.mov', '.webm'],
        'Imagens_Assets': ['.jpg', '.jpeg', '.png', '.webp', '.svg'],
        'Documentos_PDF': ['.pdf', '.txt', '.docx', '.xlsx', '.csv']
    }
    moved = 0
    for item in USER_DOWNLOADS.iterdir():
        if item.is_file():
            ext = item.suffix.lower()
            for folder, exts in extensions.items():
                if ext in exts:
                    target = USER_DOWNLOADS / folder
                    target.mkdir(exist_ok=True)
                    try:
                        shutil.move(str(item), str(target / item.name))
                        moved += 1
                    except: pass
                    break
    return f"🧹 Downloads organizados! {moved} arquivos categorizados."

def create_project_workspace(project_name: str) -> str:
    """Cria estrutura de projeto."""
    base_path = USER_DOCUMENTS / "Jarvis_Projetos" / project_name
    subfolders = ['01_Assets_Brutos', '02_Edicao_Roteiro', '03_Exportados', '04_Documentacao_Tecnica']
    try:
        for sub in subfolders:
            (base_path / sub).mkdir(parents=True, exist_ok=True)
        return f"📁 Estrutura criada em: {base_path}"
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def search_local_files(query_term: str) -> str:
    """Busca arquivos locais."""
    results = []
    search_dirs = [USER_DOWNLOADS, USER_DOCUMENTS]
    for s_dir in search_dirs:
        if s_dir.exists():
            for root, dirs, files in os.walk(s_dir):
                for file in files:
                    if query_term.lower() in file.lower():
                        results.append(os.path.join(root, file))
                        if len(results) >= 15: break
                if len(results) >= 15: break
    if not results: return f"Nenhum arquivo encontrado com o termo '{query_term}'."
    msg = f"🔍 Arquivos encontrados para '{query_term}':\n"
    for path in results: msg += f"- {path}\n"
    return msg

python_runner = PythonTools()
def request_code_execution_approval(python_code: str, user_id: str) -> str:
    PENDING_APPROVALS[user_id] = python_code
    return f"🔒 *APROVAÇÃO DE CÓDIGO NECESSÁRIA:*\n`python\n{python_code}\n`\nResponda **'autorizar'** ou **'negar'**."

# ---------------------------------------------------------------------------
# EQUIPE DE SUBAGENTES
# ---------------------------------------------------------------------------

media_agent = Agent(
    name="Silas",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[download_media_from_url, organize_downloads_folder, analyze_web_content, create_project_workspace, search_local_files, check_item_price, list_tracked_prices, add_monitored_url, list_monitored_urls],
    instructions=[
        "Especialista em mídias, downloads, raspagem de preços, geolocalização e análise de viabilidade logística.",
        "Sempre que analisar preços de insumos (seja para brigadeiros, carnes ou frutas), cruze o valor com o raio de distância ou frete com base no CEP do Wesley."
    ]
)

database_agent = Agent(
    name="Vault",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[add_quick_note, add_deadline, list_all_deadlines, update_user_profile, read_user_profile],
    instructions=[
        "Especialista em banco de dados SQLite, gestão de prazos, notas e perfil cognitivo/logístico profundo do usuário.",
        "Sempre que identificar fatos relevantes (como CEP, preferências de compra, metas), registre imediatamente com update_user_profile."
    ]
)

coder_agent = Agent(
    name="Coder",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[request_code_execution_approval],
    instructions=["Especialista técnico. Use request_code_execution_approval para submeter códigos à aprovação."]
)

jarvis_team = Team(
    name="JarvisTeam",
    model=OpenAIChat(id="gpt-4o-mini"),
    members=[media_agent, database_agent, coder_agent],
    db=SqliteDb(db_file=str(AGENT_DB_PATH)),
    add_history_to_context=True,
    num_history_runs=5,
    instructions=[
        "Você é o Jarvis, o assistente pessoal principal de comando de Wesley Cruz conectado via Telegram.",
        "--- PERFIL E CONTEXTO PERMANENTE DO WESLEY ---",
        "- Família: Casado, filha de 12 anos e filho de 14 meses.",
        "- Negócios: Fabricação própria e venda de brigadeiros (com a esposa). Futura expansão para controle de suprimentos de casa (carnes, frutas, etc.).",
        "- Grande meta: Vender agentes autônomos e automações de IA por R$ 1.500 setup + R$ 1.000/mês.",
        "- Estilo de vida: Corrida de rua, calistenia, musculação, karatê (faixa marrom), medicinas da floresta, natureza, idiomas, filmes e edição de vídeo.",
        "- Técnico: Python, Docker, Agno.",
        "--- DIRETRIZ DE COMPORTAMENTO E LOGÍSTICA ---",
        "1. Atue estritamente como conselheiro estratégico, analítico, crítico e proativo. Nunca busque validação automática. Aponte riscos, cobre metas e faça contrapontos construtivos.",
        "2. ANÁLISE DE VIABILIDADE LOGÍSTICA: Sempre que avaliar preços de produtos ou insumos, verifique a localização/CEP do Wesley. Se a diferença de preço for pequena mas a distância ou o frete forem altos, alerte explicitamente que o deslocamento anula a economia (foco estrito em margem de lucro e eficiência)."
    ],
    markdown=True
)

# ---------------------------------------------------------------------------
# TAREFAS PROATIVAS
# ---------------------------------------------------------------------------
async def proactive_deadline_check():
    global GLOBAL_BOT_APP
    if not GLOBAL_BOT_APP: return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, task_description, due_date FROM deadlines WHERE status = 'pendente' AND due_date <= date('now', '+3 days')")
        upcoming = cursor.fetchall()
        conn.close()

        if upcoming:
            for did, desc, ddate in upcoming:
                response = jarvis_team.run(f"Cobre o Wesley proativamente sobre o prazo próximo: '{desc}' para {ddate}.", session_id="proactive_deadline")
                conn_db = sqlite3.connect(AGENT_DB_PATH)
                cur_db = conn_db.cursor()
                cur_db.execute("SELECT DISTINCT session_id FROM agent_sessions LIMIT 1")
                row_chat = cur_db.fetchone()
                conn_db.close()
                if row_chat:
                    await GLOBAL_BOT_APP.bot.send_message(chat_id=int(row_chat[0]), text=f"🚨 *Alerta Proativo (Prazo):*\n\n{response.content}", parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erro nos deadlines: {str(e)}")

async def scheduled_price_check():
    global GLOBAL_BOT_APP
    if not GLOBAL_BOT_APP: return
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT item_name, url FROM monitored_urls")
        items = cursor.fetchall()
        conn.close()

        if not items: return

        report = "🏷️ *Relatório Logístico de Preços (Background):*\n\n"
        for name, url in items:
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                requests.get(url, headers=headers, timeout=10)
                report += f"✅ {name}: Checado com análise de raio logístico.\n"
            except:
                report += f"⚠️ {name}: Falha temporária.\n"

        conn_db = sqlite3.connect(AGENT_DB_PATH)
        cur_db = conn_db.cursor()
        cur_db.execute("SELECT DISTINCT session_id FROM agent_sessions LIMIT 1")
        row_chat = cur_db.fetchone()
        conn_db.close()

        if row_chat:
            await GLOBAL_BOT_APP.bot.send_message(chat_id=int(row_chat[0]), text=report, parse_mode="Markdown")
    except Exception as e:
        logging.error(f"Erro no monitoramento logístico: {str(e)}")

# ---------------------------------------------------------------------------
# MANIPULADORES DE MENSAGEM
# ---------------------------------------------------------------------------
async def process_user_input(update: Update, text_content: str):
    user_id = str(update.effective_user.id)
    text_lower = text_content.lower().strip()

    if user_id in PENDING_APPROVALS:
        if "autorizar" in text_lower or "sim" in text_lower or "pode" in text_lower:
            code_to_run = PENDING_APPROVALS.pop(user_id)
            await update.message.reply_text("🚀 Executando código autorizado...", parse_mode="Markdown")
            try:
                result = python_runner.run_code(code_to_run)
                await update.message.reply_text(f"✅ *Resultado:*\n`	ext\n{result}\n`", parse_mode="Markdown")
            except Exception as e:
                await update.message.reply_text(f"❌ Erro: {str(e)}")
            return
        elif "negar" in text_lower or "não" in text_lower or "cancelar" in text_lower:
            PENDING_APPROVALS.pop(user_id, None)
            await update.message.reply_text("🛑 Execução cancelada.", parse_mode="Markdown")
            return

    await update.message.chat.send_action("typing")
    try:
        response = jarvis_team.run(text_content, session_id=user_id)
        reply_text = response.content if response and response.content else "Comando processado, chefe."
        await update.message.reply_text(reply_text, parse_mode="Markdown")
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
        
        await update.message.reply_text(f"🎙️ *Transcrito:* _{transcript.text}_", parse_mode="Markdown")
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
    scheduler.add_job(proactive_deadline_check, 'interval', hours=6)
    scheduler.add_job(scheduled_price_check, 'interval', days=1)
    scheduler.start()

    print("🤖 Jarvis Team (Com Análise Logística e Proximidade) Ativo...")
    app.run_polling()

if __name__ == '__main__':
    main()
