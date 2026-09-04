# -*- coding: utf-8 -*-
import time
import schedule
from modules.personal.inbox_watcher import process_inbox
from modules.personal.exporter_cli import export_to_markdown
from core.storage.logger import log_event

def job_inbox():
    print("\n⏰ [Jarvis Scheduler] Executando varredura automática do Inbox...")
    try:
        process_inbox()
    except Exception as e:
        log_event("ERROR", "scheduler", f"Erro no inbox automático: {e}")

def job_export():
    print("\n⏰ [Jarvis Scheduler] Executando exportação diária de backup...")
    try:
        export_to_markdown()
    except Exception as e:
        log_event("ERROR", "scheduler", f"Erro na exportação automática: {e}")

def start_scheduler():
    print("🧠 [Jarvis Life OS] Agendador de tarefas em segundo plano iniciado...")
    print("🔹 Monitorando Inbox a cada 1 minuto.")
    print("🔹 Exportando relatório diário a cada 1 hora (ou ajuste conforme desejar).")
    print("Pressione CTRL+C para encerrar o agendador.\n")

    # Define as rotinas
    schedule.every(1).minutes.do(job_inbox)
    schedule.every(1).hours.do(job_export)

    # Loop principal do daemon
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == "__main__":
    start_scheduler()