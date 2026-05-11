"""
Punto de entrada principal.

Ejecutar:
    python main.py

Requisitos:
    pip install customtkinter   (opcional, la app usa tkinter estándar)
"""

import sys
import tkinter as tk


def check_python_version() -> None:
    if sys.version_info < (3, 8):
        print("ERROR: Se requiere Python 3.8 o superior.")
        sys.exit(1)


def main() -> None:
    check_python_version()
    from gui.main_window import MainWindow
    app = MainWindow()
    app.run()


if __name__ == "__main__":
    main()
