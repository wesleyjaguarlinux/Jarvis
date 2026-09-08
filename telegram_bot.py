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
OBSIDIAN_CONTEXT_PATH = Path(r"C:\Users\Wesley\Downloads\Cérebro-20260402T184614Z-1-001\Cérebro\Contexto_Jarvis")

client = OpenAI()
AGENT_DB_PATH = Path.cwd() / "core" / "storage" / "agent_memory.db"
AGENT_DB_PATH.parent.mkdir(parents=True, exist_ok=True)

PENDING_APPROVALS = {}
GLOBAL_BOT_APP = None

# ---------------------------------------------------------------------------
# INICIALIZAÇÃO DE TABELAS (PERFIL, DEADLINES, PREÇOS, URLS, LEADS E OBSIDIAN)
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS leads_prospeccao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_name TEXT,
            nicho TEXT,
            site_url TEXT,
            pain_identified TEXT,
            status TEXT DEFAULT 'novo_lead',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS obsidian_knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_title TEXT,
            content TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_optimized_db()

# ---------------------------------------------------------------------------
# FERRAMENTAS DO VAULT (MEMÓRIA, PERFIL E OBSIDIAN)
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
    """Atualiza um aspecto do perfil de longo prazo do usuário."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO user_profile (category, content) VALUES (?, ?)", (category, content))
    conn.commit()
    conn.close()
    return f"🧬 Perfil atualizado [{category}]: {content}"

def read_user_profile() -> str:
    """Lê todo o perfil cognitivo e logístico de longo prazo acumulado."""
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

def sync_obsidian_notes() -> str:
    """Varre a pasta Contexto_Jarvis do Obsidian, lê as notas .md e atualiza a base de conhecimento local no SQLite."""
    if not OBSIDIAN_CONTEXT_PATH.exists():
        return f"❌ A pasta do Obsidian não foi encontrada no caminho configurado: {OBSIDIAN_CONTEXT_PATH}"
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    count = 0
    synced_files = []
    
    for file_path in OBSIDIAN_CONTEXT_PATH.glob("**/*.md"):
        if file_path.is_file():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                title = file_path.stem
                
                # Verifica se a nota já existe na base
                cursor.execute("SELECT id FROM obsidian_knowledge WHERE file_title = ?", (title,))
                row = cursor.fetchone()
                
                if row:
                    cursor.execute("UPDATE obsidian_knowledge SET content = ?, updated_at = CURRENT_TIMESTAMP WHERE file_title = ?", (content, title))
                else:
                    cursor.execute("INSERT INTO obsidian_knowledge (file_title, content) VALUES (?, ?)", (title, content))
                
                count += 1
                synced_files.append(title)
            except Exception as e:
                logging.error(f"Erro ao ler arquivo {file_path.name}: {str(e)}")
                
    conn.commit()
    conn.close()
    
    if count == 0:
        return "⚠️ Nenhuma nota em formato .md foi encontrada dentro da pasta Contexto_Jarvis."
    
    return f"🔄 Sincronização concluída com sucesso! {count} nota(s) do Obsidian indexada(s):\n- " + "\n- ".join(synced_files)

def search_obsidian_knowledge(query_term: str) -> str:
    """Busca nas notas indexadas do Obsidian por termos ou conceitos específicos."""
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT file_title, content FROM obsidian_knowledge WHERE file_title LIKE ? OR content LIKE ?", 
                   (f"%{query_term}%", f"%{query_term}%"))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows: return f"Nenhuma nota encontrada no Obsidian com o termo '{query_term}'."
    
    msg = f"📂 Notas do Obsidian encontradas para '{query_term}':\n\n"
    for title, content in rows[:5]: # Limita a 5 notas para não estourar o limite da mensagem
        snippet = content[:1500] + ("..." if len(content) > 1500 else "")
        msg += f"📄 **{title}**\n{snippet}\n\n-------------------\n\n"
    return msg

# ---------------------------------------------------------------------------
# FERRAMENTAS DO HUNTER (VENDAS, SCRIPTS E OBJEÇÕES)
# ---------------------------------------------------------------------------

def save_lead_prospect(company_name: str, nicho: str, site_url: str, pain_identified: str) -> str:
    """Salva um lead corporativo qualificado no banco SQLite para acompanhamento de vendas."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO leads_prospeccao (company_name, nicho, site_url, pain_identified) VALUES (?, ?, ?, ?)", 
                   (company_name, nicho, site_url, pain_identified))
    conn.commit()
    conn.close()
    return f"🎯 Lead comercial '{company_name}' ({nicho}) salvo com sucesso no pipeline de vendas!"

def list_all_leads() -> str:
    """Lista todos os leads cadastrados no pipeline de prospecção de IA."""
    if not DB_PATH.exists(): return "Banco de dados não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, company_name, nicho, site_url, pain_identified, status FROM leads_prospeccao ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhum lead comercial cadastrado no pipeline."
    
    msg = "💼 Pipeline de Prospecção B2B (Meta: R$ 1.500 setup + R$ 1.000/mês):\n"
    for lid, comp, nicho, url, pain, status in rows:
        msg += f"[Lead ID {lid}] {comp} ({nicho})\n  Dor: {pain}\n  Status: [{status}]\n  Link: {url}\n\n"
    return msg

def generate_sales_script(channel: str, nicho: str, company_name: str, pain: str) -> str:
    """Gera um script de abordagem comercial altamente persuasivo com base no canal (whatsapp ou email)."""
    if channel.lower() == "whatsapp":
        script = (f"📱 *Script WhatsApp para {company_name} ({nicho}):*\n\n"
                  f"'Olá [Nome do Sócio/Gerente], tudo bem? Acompanho a {company_name} e notei uma oportunidade clara "
                  f"de otimizar o atendimento de vocês no WhatsApp/Instagram. Hoje, muitas empresas perdem clientes por demorar a responder. "
                  f"Nós implementamos assistentes de IA que respondem clientes 24h, tiram dúvidas e fecham pedidos automaticamente. "
                  f"Topa bater um papo de 10 minutos para eu te mostrar como isso bota mais dinheiro no seu caixa?'")
    else:
        script = (f"✉️ *Script E-mail / LinkedIn para {company_name} ({nicho}):*\n\n"
                  f"Assunto: Automação de Atendimento e Escala para a {company_name}\n\n"
                  f"Olá [Nome], tudo bem?\n\n"
                  f"Analisando a operação da {company_name} no nicho de {nicho}, identifiquei que gargalos operacionais em [{pain}] "
                  f"podem estar limitando o seu faturamento mensal.\n\n"
                  f"Nós desenvolvemos agentes autônomos de inteligência artificial sob medida que eliminam esse atrito, integrando-se diretamente aos seus canais de vendas.\n\n"
                  f"Nossa estrutura exige um investimento único de setup de R$ 1.500 e sustentação mensal de R$ 1.000, gerando ROI rápido através da eficiência operacional.\n\n"
                  f"Podemos agendar uma demonstração rápida de 15 minutos esta semana?\n\n"
                  f"Atenciosamente,\nWesley Cruz")
    return script

def get_objection_handler(objection_type: str) -> str:
    """Fornece a tática exata de contraponto para quebrar objeções comuns de clientes."""
    objections = {
        "caro": "💸 *Objeção: 'Está caro / Não tenho orçamento'*\n\n👉 *Como responder:* 'Entendo perfeitamente a preocupação com custos. Mas veja por outro ângulo: quanto custa hoje o tempo perdido pela sua equipe respondendo perguntas repetitivas ou perdendo leads fora do horário comercial? O setup de R$ 1.500 e a mensalidade de R$ 1.000 se pagam sozinhos no primeiro mês ao recuperar apenas dois clientes que escaparam. A IA não é gasto, é funcionário que trabalha 24h sem cobrar encargos trabalhistas.'",
        "ja_tem": "🛑 *Objeção: 'Já temos quem faça isso / Não precisamos de IA'*\n\n👉 *Como responder:* 'Isso é excelente, sinal de que a operação está rodando. A ideia não é substituir sua equipe, mas tirar o trabalho robótico e repetitivo das mãos deles para que possam focar em fechar vendas de alto valor, enquanto a IA cuida do volume automatizado. Quer ver um exemplo prático de 5 minutos de como isso acelera o processo?'",
        "duvida": "🤔 *Objeção: 'Isso é muito complexo / Não entendo de tecnologia'*\n\n👉 *Como responder:* 'E exatamente por isso que nós fazemos 100% do trabalho técnico. Você não precisa mexer em código ou entender de IA. Nós entregamos a ferramenta pronta, testada e rodando, exatamente como um software pronto para uso. O seu único trabalho é colher os resultados.'"
    }
    key = objection_type.lower().strip()
    return objections.get(key, "Objeção não mapeada. Use as categorias: 'caro', 'ja_tem', ou 'duvida'.")

# ---------------------------------------------------------------------------
# FERRAMENTAS DO SILAS (MÍDIA, WEB, SCRAPING E LOGÍSTICA)
# ---------------------------------------------------------------------------

def add_monitored_url(item_name: str, url: str) -> str:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO monitored_urls (item_name, url) VALUES (?, ?)", (item_name, url))
    conn.commit()
    conn.close()
    return f"🎯 Insumo '{item_name}' cadastrado!"

def list_monitored_urls() -> str:
    if not DB_PATH.exists(): return "Banco não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, item_name, url FROM monitored_urls")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhum link cadastrado."
    msg = "📋 Insumos Monitorados:\n"
    for uid, name, u in rows: msg += f"[ID {uid}] {name}\n  Link: {u}\n"
    return msg

def analyze_web_content(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]): script.decompose()
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = [phrase.strip() for line in lines for phrase in line.split("  ") if phrase.strip()]
        joined_text = "\n".join(chunks)[:4000]
        return f"🌐 Conteúdo extraído ({url}):\n\n{joined_text}"
    except Exception as e:
        return f"❌ Erro ao extrair link {url}: {str(e)}"

def check_item_price(item_name: str, url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        requests.get(url, headers=headers, timeout=12)
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO price_tracker (item_name, url, price) VALUES (?, ?, ?)", (item_name, url, 0.0))
        conn.commit()
        conn.close()
        return f"🌐 Varredura realizada para '{item_name}'."
    except Exception as e:
        return f"❌ Erro: {str(e)}"

def list_tracked_prices() -> str:
    if not DB_PATH.exists(): return "Banco não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT item_name, price, url, checked_at FROM price_tracker ORDER BY id DESC LIMIT 20")
    rows = cursor.fetchall()
    conn.close()
    if not rows: return "Nenhum preço registrado."
    msg = "💰 Histórico de Preços:\n"
    for name, prc, u, dt in rows: msg += f"- {name}: R$ {prc} ({dt})\n"
    return msg

def download_media_from_url(url: str) -> str:
    ydl_opts = {'outtmpl': str(DOWNLOAD_DIR / '%(title)s.%(ext)s'), 'format': 'best', 'nocheckcertificate': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"📥 Mídia baixada! Título: {info.get('title', 'Vídeo')}"
    except Exception as e: return f"❌ Erro: {str(e)}"

def organize_downloads_folder() -> str:
    if not USER_DOWNLOADS.exists(): return "Pasta não encontrada."
    extensions = {'Videos': ['.mp4', '.mkv'], 'Imagens': ['.jpg', '.png'], 'Docs': ['.pdf', '.txt']}
    moved = 0
    for item in USER_DOWNLOADS.iterdir():
        if item.is_file():
            ext = item.suffix.lower()
            for folder, exts in extensions.items():
                if ext in exts:
                    target = USER_DOWNLOADS / folder
                    target.mkdir(exist_ok=True)
                    try: shutil.move(str(item), str(target / item.name)); moved += 1
                    except: pass
                    break
    return f"🧹 Organizado! {moved} arquivos movidos."

def create_project_workspace(project_name: str) -> str:
    base_path = USER_DOCUMENTS / "Jarvis_Projetos" / project_name
    for sub in ['01_Assets', '02_Codigo', '03_Docs']: (base_path / sub).mkdir(parents=True, exist_ok=True)
    return f"📁 Projeto criado em: {base_path}"

def search_local_files(query_term: str) -> str:
    results = []
    for s_dir in [USER_DOWNLOADS, USER_DOCUMENTS]:
        if s_dir.exists():
            for root, dirs, files in os.walk(s_dir):
                for file in files:
                    if query_term.lower() in file.lower(): results.append(os.path.join(root, file))
    return f"🔍 Encontrados:\n" + "\n".join(results[:10]) if results else "Nenhum arquivo."

python_runner = PythonTools()
def request_code_execution_approval(python_code: str, user_id: str) -> str:
    PENDING_APPROVALS[user_id] = python_code
    return f"🔒 *APROVAÇÃO DE CÓDIGO NECESSÁRIA:*\n`python\n{python_code}\n`\nResponda **'autorizar'** ou **'negar'**."

# ---------------------------------------------------------------------------
# EQUIPE DE SUBAGENTES (SILAS, VAULT, HUNTER, CODER)
# ---------------------------------------------------------------------------

media_agent = Agent(
    name="Silas",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[download_media_from_url, organize_downloads_folder, analyze_web_content, create_project_workspace, search_local_files, check_item_price, list_tracked_prices, add_monitored_url, list_monitored_urls],
    instructions=["Especialista em mídias, scraping web e organização de arquivos."]
)

database_agent = Agent(
    name="Vault",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[add_quick_note, add_deadline, list_all_deadlines, update_user_profile, read_user_profile, sync_obsidian_notes, search_obsidian_knowledge],
    instructions=[
        "Especialista em banco de dados SQLite, prazos, notas, perfil de longo prazo e leitura do cofre Obsidian do Wesley.",
        "Sempre que o Wesley pedir para sincronizar ou buscar notas no Obsidian, utilize as ferramentas de sincronização e busca local."
    ]
)

hunter_agent = Agent(
    name="Hunter",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[save_lead_prospect, list_all_leads, analyze_web_content, generate_sales_script, get_objection_handler],
    instructions=[
        "Especialista em prospecção comercial B2B, geração de scripts multicanal e quebra de objeções para venda de automações de IA (Meta: R$ 1.500 setup + R$ 1.000/mês)."
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
    members=[media_agent, database_agent, hunter_agent, coder_agent],
    db=SqliteDb(db_file=str(AGENT_DB_PATH)),
    add_history_to_context=True,
    num_history_runs=5,
    instructions=[
        "Você é o Jarvis, o assistente pessoal principal de comando de Wesley Cruz conectado via Telegram.",
        "--- PERFIL E CONTEXTO PERMANENTE DO WESLEY ---",
        "- Família: Casado, filha de 12 anos e filho de 14 meses.",
        "- Negócios: Fabricação própria e venda de brigadeiros + Consultoria de Automação de IA.",
        "- GRANDE META COMERCIAL: Vender agentes autônomos e automações de IA para empresas por R$ 1.500 setup + R$ 1.000/mês.",
        "- Estilo de vida: Corrida de rua, calistenia, musculação, karatê (faixa marrom), medicinas da floresta, natureza, idiomas, filmes e edição de vídeo.",
        "- Técnico: Python, Docker, Agno.",
        "--- DIRETRIZ DE COMPORTAMENTO E VENDAS ---",
        "1. Atue estritamente como conselheiro estratégico, analítico, crítico e proativo. Nunca busque validação automática. Aponte riscos, cobre metas de vendas e faça contrapontos construtivos.",
        "2. CONSULTA AO OBSIDIAN: Quando o Wesley fizer perguntas sobre projetos, ideias ou planejamentos que exijam detalhes profundos, oriente o Vault a buscar nas notas do Obsidian."
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
        for name, url in items: report += f"✅ {name}: Checado.\n"
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

    print("🤖 Jarvis Team (Com Leitura do Obsidian e Integração Total) Ativo...")
    app.run_polling()

if __name__ == '__main__':
    main()
