# -*- coding: utf-8 -*-
import sys
import argparse
from modules.personal.reporter import generate_report
from modules.personal.habits_cli import list_pending_habits, complete_habit
from modules.personal.notes_cli import add_note, list_notes

def main():
    parser = argparse.ArgumentParser(description="Jarvis Life OS - O seu Segundo Cerebro")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponiveis")

    # Comando: report
    subparsers.add_parser("report", help="Gera o relatorio consolidado de produtividade")

    # Comando: habits
    habits_parser = subparsers.add_parser("habits", help="Gerenciamento de habitos e metas")
    habits_parser.add_argument("--list", action="store_true", help="Lista habitos pendentes")
    habits_parser.add_argument("--done", type=int, help="Marca um habito como concluido pelo ID")

    # Comando: notes
    notes_parser = subparsers.add_parser("notes", help="Gerenciamento de notas rapidas")
    notes_parser.add_argument("--add", nargs=2, metavar=('TAG', 'CONTEUDO'), help="Adiciona nova nota")
    notes_parser.add_argument("--list", action="store_true", help="Lista todas as notas")

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
    else:
        print("🧠 [Jarvis Life OS] Bem-vindo ao nucleo do sistema.")
        print("Use 'python main.py -h' para ver os comandos disponiveis.")

if __name__ == "__main__":
    main()