# -*- coding: utf-8 -*-
import sys
import argparse
from modules.personal.reporter import generate_report
from modules.personal.habits_cli import list_pending_habits, complete_habit

def main():
    parser = argparse.ArgumentParser(description="Jarvis Life OS - O seu Segundo Cerebro")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando: report
    subparsers.add_parser("report", help="Gera o relatorio consolidado de produtividade")

    # Comando: habits
    habits_parser = subparsers.add_parser("habits", help="Gerenciamento de habitos e metas")
    habits_parser.add_argument("--list", action="store_true", help="Lista habitos pendentes")
    habits_parser.add_argument("--done", type=int, help="Marca um habito como concluido pelo ID")

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
    else:
        print("🧠 [Jarvis Life OS] Bem-vindo ao nucleo do sistema.")
        print("Use 'python main.py -h' para ver os comandos disponiveis.")

if __name__ == "__main__":
    main()