# -*- coding: utf-8 -*-
import sys
import argparse
from modules.personal.reporter import generate_report
from modules.personal.habits_cli import list_pending_habits, complete_habit
from modules.personal.notes_cli import add_note, list_notes
from modules.personal.inbox_watcher import process_inbox
from modules.personal.search_cli import search_database
from modules.personal.web_fetcher import fetch_and_save_url
from modules.personal.exporter_cli import export_to_markdown
from modules.personal.scheduler import start_scheduler

def main():
    parser = argparse.ArgumentParser(description="Jarvis Life OS - O seu Segundo Cerebro")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponiveis")

    subparsers.add_parser("report", help="Gera o relatorio consolidado de produtividade")

    habits_parser = subparsers.add_parser("habits", help="Gerenciamento de habitos e metas")
    habits_parser.add_argument("--list", action="store_true", help="Lista habitos pendentes")
    habits_parser.add_argument("--done", type=int, help="Marca um habito como concluido pelo ID")

    notes_parser = subparsers.add_parser("notes", help="Gerenciamento de notas rapidas")
    notes_parser.add_argument("--add", nargs=2, metavar=('TAG', 'CONTEUDO'), help="Adiciona nova nota")
    notes_parser.add_argument("--list", action="store_true", help="Lista todas as notas")

    subparsers.add_parser("inbox", help="Processa e ingere arquivos pendentes da pasta inbox")

    search_parser = subparsers.add_parser("search", help="Busca inteligente no banco de dados")
    search_parser.add_argument("term", type=str, help="Termo a ser buscado")

    fetch_parser = subparsers.add_parser("fetch", help="Captura conteudo de uma URL e salva nas notas")
    fetch_parser.add_argument("url", type=str, help="Link da pagina web")
    fetch_parser.add_argument("--tag", type=str, default="web", help="Tag opcional (padrao: web)")

    subparsers.add_parser("export", help="Exporta o relatorio completo do sistema para Markdown")
    subparsers.add_parser("daemon", help="Inicia o agendador autonomo de tarefas em segundo plano")

    args = parser.parse_args()

    if args.command == "report":
        generate_report()
    elif args.command == "habits":
        if args.list:
            list_pending_habits()
        elif args.done is not None:
            complete_habit(args.done)
        else:
            print("⚠️ Uso incorreto. Use: python main.py habits --list ou --done <ID>")
    elif args.command == "notes":
        if args.add:
            tag, content = args.add
            add_note(tag, content)
        elif args.list:
            list_notes()
        else:
            print("⚠️ Uso incorreto. Use: python main.py notes --add <TAG> <CONTEUDO> ou --list")
    elif args.command == "inbox":
        process_inbox()
    elif args.command == "search":
        search_database(args.term)
    elif args.command == "fetch":
        fetch_and_save_url(args.url, args.tag)
    elif args.command == "export":
        export_to_markdown()
    elif args.command == "daemon":
        start_scheduler()
    else:
        print("🧠 [Jarvis Life OS] Bem-vindo ao nucleo do sistema.")
        print("Use 'python main.py -h' para ver os comandos disponiveis.")

if __name__ == "__main__":
    main()