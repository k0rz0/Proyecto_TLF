"""
Ventana principal de la aplicación.

Layout:
    ┌─────────────────────────────────────────┐
    │  HEADER: título + info                  │
    ├─────────────────────────────────────────┤
    │  Notebook (3 pestañas)                  │
    │    Tab 1: Búsqueda en texto             │
    │    Tab 2: Formulario interactivo        │
    │    Tab 3: Simulador AFD                 │
    ├─────────────────────────────────────────┤
    │  STATUS BAR                             │
    └─────────────────────────────────────────┘
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk

from gui.tab_automata import AutomataTab
from gui.tab_form import FormTab
from gui.tab_search import SearchTab
from utils.history import HistoryManager


class MainWindow:
    """
    Clase que encapsula la ventana principal de la aplicación.

    Crea el Tk root, aplica estilos, construye el notebook con las
    tres pestañas y mantiene la barra de estado global.
    """

    APP_TITLE   = "Analizador Léxico y Sintáctico — Teoría de Lenguajes Formales"
    APP_VERSION = "1.0.0"

    def __init__(self) -> None:
        self._root = tk.Tk()
        self._history = HistoryManager()
        self._setup_root()
        self._apply_styles()
        self._build_ui()

    # ------------------------------------------------------------------
    # Configuración de la ventana
    # ------------------------------------------------------------------

    def _setup_root(self) -> None:
        self._root.title(self.APP_TITLE)
        self._root.geometry("1150x780")
        self._root.minsize(900, 600)
        # Icono textual (sin imagen externa)
        try:
            self._root.iconbitmap(default="")
        except Exception:
            pass

        self._root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _apply_styles(self) -> None:
        style = ttk.Style(self._root)
        # Intentar usar un tema moderno
        available = style.theme_names()
        for preferred in ("vista", "xpnative", "clam", "alt", "default"):
            if preferred in available:
                style.theme_use(preferred)
                break

        # Personalizar colores
        style.configure("TNotebook",        background="#E3F2FD")
        style.configure("TNotebook.Tab",    padding=[12, 6], font=("Segoe UI", 10, "bold"))
        style.configure("TLabelframe",      padding=6)
        style.configure("TLabelframe.Label",font=("Segoe UI", 9, "bold"), foreground="#1565C0")
        style.configure("Accent.TButton",   font=("Segoe UI", 10, "bold"))

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Header ────────────────────────────────────────────────────
        header = tk.Frame(self._root, bg="#1565C0", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)

        tk.Label(
            header,
            text="⚙  Analizador Léxico y Sintáctico",
            font=("Segoe UI", 14, "bold"),
            bg="#1565C0", fg="white",
        ).pack(side=tk.LEFT, padx=16, pady=12)

        tk.Label(
            header,
            text=(
                "Autómatas Finitos Deterministas  ·  "
                "Análisis Léxico  ·  Análisis Sintáctico"
            ),
            font=("Segoe UI", 9),
            bg="#1565C0", fg="#BBDEFB",
        ).pack(side=tk.LEFT, padx=0)

        tk.Label(
            header,
            text=f"v{self.APP_VERSION}",
            font=("Segoe UI", 8),
            bg="#1565C0", fg="#90CAF9",
        ).pack(side=tk.RIGHT, padx=16)

        # ── Notebook ──────────────────────────────────────────────────
        notebook = ttk.Notebook(self._root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        self._tab_search   = SearchTab(notebook,   history=self._history)
        self._tab_form     = FormTab(notebook,     history=self._history)
        self._tab_automata = AutomataTab(notebook)

        notebook.add(self._tab_search,   text="  🔍 Búsqueda en Texto  ")
        notebook.add(self._tab_form,     text="  📋 Formulario Interactivo  ")
        notebook.add(self._tab_automata, text="  🤖 Simulador AFD  ")

        # ── Status bar ────────────────────────────────────────────────
        status = tk.Frame(self._root, bg="#E3F2FD", bd=1, relief=tk.SUNKEN)
        status.pack(fill=tk.X, side=tk.BOTTOM)

        self._status_var = tk.StringVar(
            value="Listo  |  Uso: escribe texto y usa la pestaña 'Búsqueda'  "
                  "o prueba el Formulario o el Simulador AFD."
        )
        tk.Label(
            status, textvariable=self._status_var,
            bg="#E3F2FD", fg="#1565C0",
            font=("Segoe UI", 8), anchor=tk.W,
        ).pack(side=tk.LEFT, padx=6, pady=2)

        tk.Label(
            status,
            text=(
                "Teoría de Lenguajes Formales  ·  AFD implementado sin librería 're'  "
                f"·  Python 3.11+"
            ),
            bg="#E3F2FD", fg="#78909C",
            font=("Segoe UI", 8),
        ).pack(side=tk.RIGHT, padx=6)

        # Menú
        self._build_menu()

    def _build_menu(self) -> None:
        menubar = tk.Menu(self._root)

        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(
            label="Salir", command=self._on_close, accelerator="Alt+F4"
        )
        menubar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Historial
        hist_menu = tk.Menu(menubar, tearoff=0)
        hist_menu.add_command(label="Ver historial", command=self._show_history)
        hist_menu.add_command(label="Limpiar historial", command=self._clear_history)
        menubar.add_cascade(label="Historial", menu=hist_menu)

        # Menú Acerca de
        about_menu = tk.Menu(menubar, tearoff=0)
        about_menu.add_command(label="Acerca de", command=self._show_about)
        menubar.add_cascade(label="Acerca de", menu=about_menu)

        self._root.config(menu=menubar)

    # ------------------------------------------------------------------
    # Eventos y diálogos
    # ------------------------------------------------------------------

    def _on_close(self) -> None:
        if messagebox.askokcancel("Salir", "¿Deseas cerrar la aplicación?"):
            self._root.destroy()

    def _show_about(self) -> None:
        messagebox.showinfo(
            "Acerca de",
            f"{self.APP_TITLE}\n"
            f"Versión: {self.APP_VERSION}\n\n"
            "Proyecto Final — Teoría de Lenguajes Formales\n\n"
            "Implementa:\n"
            "  • Autómatas Finitos Deterministas (AFD)\n"
            "  • Análisis Léxico (Lexer / Scanner)\n"
            "  • Análisis Sintáctico (Parser)\n"
            "  • Validación sin librería 're'\n\n"
            "Patrones reconocidos:\n"
            "  EMAIL · TELÉFONO · FECHA · URL\n"
            "  PLACA · USUARIO · CONTRASEÑA\n",
        )

    def _show_history(self) -> None:
        entries = self._history.get_recent(30)
        if not entries:
            messagebox.showinfo("Historial", "El historial está vacío.")
            return

        win = tk.Toplevel(self._root)
        win.title("Historial de validaciones")
        win.geometry("700x400")

        cols = ("Fecha", "Tipo entrada", "Tipo token", "Valor", "Válido", "Errores")
        tree = ttk.Treeview(win, columns=cols, show="headings")
        widths = (130, 80, 100, 200, 60, 200)
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w)

        for e in entries:
            tree.insert("", tk.END, values=(
                e.timestamp, e.input_type, e.token_type,
                e.value, "Sí" if e.is_valid else "No",
                "; ".join(e.errors),
            ))

        sb = ttk.Scrollbar(win, command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

    def _clear_history(self) -> None:
        if messagebox.askyesno("Limpiar historial", "¿Eliminar todo el historial?"):
            self._history.clear()
            messagebox.showinfo("Listo", "Historial limpiado.")

    # ------------------------------------------------------------------
    # Punto de entrada
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Inicia el loop principal de tkinter."""
        self._root.mainloop()
