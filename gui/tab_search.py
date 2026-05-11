"""
Pestaña 1 — Búsqueda de Patrones en Texto.

Permite al usuario:
- Escribir texto o cargar un archivo .txt
- Analizar el texto con el Lexer
- Ver todos los tokens encontrados en la tabla de ResultPanel
- Ver el árbol sintáctico al seleccionar un token
- Exportar resultados a TXT, CSV o JSON
"""

from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import List, Optional

from gui.components.result_panel import ResultPanel
from lexical.lexer import Lexer
from lexical.token_types import Token
from syntax.parser import SyntaxParser
from utils.exporter import Exporter
from utils.history import HistoryManager


class SearchTab(ttk.Frame):
    """
    Pestaña de búsqueda y análisis de patrones en texto libre.
    """

    def __init__(self, master: tk.Widget, history: HistoryManager, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._lexer   = Lexer()
        self._parser  = SyntaxParser()
        self._history = history
        self._tokens: List[Token] = []
        self._current_file: Optional[str] = None
        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Barra de herramientas superior ─────────────────────────────
        toolbar = ttk.Frame(self, relief=tk.RAISED, borderwidth=1)
        toolbar.pack(fill=tk.X, padx=4, pady=4)

        ttk.Button(toolbar, text="📂 Abrir archivo",
                   command=self._open_file).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🔍 Analizar",
                   command=self._analyze).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="🗑 Limpiar",
                   command=self._clear).pack(side=tk.LEFT, padx=2)

        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=2)

        ttk.Label(toolbar, text="Exportar:").pack(side=tk.LEFT)
        ttk.Button(toolbar, text="TXT",
                   command=lambda: self._export("txt")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="CSV",
                   command=lambda: self._export("csv")).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="JSON",
                   command=lambda: self._export("json")).pack(side=tk.LEFT, padx=2)

        # ── Panel principal: split horizontal ──────────────────────────
        paned = ttk.PanedWindow(self, orient=tk.VERTICAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=4)

        # ── Área de texto ──────────────────────────────────────────────
        input_frame = ttk.LabelFrame(paned, text="Texto a analizar")
        paned.add(input_frame, weight=1)

        # Modo de análisis
        mode_bar = ttk.Frame(input_frame)
        mode_bar.pack(fill=tk.X, padx=4, pady=2)

        self._mode_var = tk.StringVar(value="word")
        ttk.Radiobutton(
            mode_bar, text="Por palabras (recomendado)",
            variable=self._mode_var, value="word"
        ).pack(side=tk.LEFT)
        ttk.Radiobutton(
            mode_bar, text="Barrido continuo",
            variable=self._mode_var, value="scan"
        ).pack(side=tk.LEFT, padx=10)

        self._text_input = tk.Text(
            input_frame, height=8, wrap=tk.WORD,
            font=("Consolas", 11), bg="#FAFAFA"
        )
        sb = ttk.Scrollbar(input_frame, command=self._text_input.yview)
        self._text_input.configure(yscrollcommand=sb.set)
        self._text_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4, pady=4)
        sb.pack(side=tk.RIGHT, fill=tk.Y, pady=4)

        # Resaltado de colores en el texto
        self._text_input.tag_configure("highlight", background="#FFF9C4")

        # ── Panel de resultados ────────────────────────────────────────
        self._result_panel = ResultPanel(paned)
        paned.add(self._result_panel, weight=2)

        # ── Barra de estado ────────────────────────────────────────────
        self._status_var = tk.StringVar(value="Listo. Escribe o carga un archivo y presiona Analizar.")
        ttk.Label(self, textvariable=self._status_var,
                  relief=tk.SUNKEN, anchor=tk.W).pack(
            fill=tk.X, side=tk.BOTTOM, padx=4, pady=2
        )

        # Texto de ejemplo
        self._load_example()

    # ------------------------------------------------------------------
    # Acciones
    # ------------------------------------------------------------------

    def _load_example(self) -> None:
        example = (
            "Contáctenos en soporte@empresa.com o en admin@universidad.edu.co\n"
            "Teléfono: 3001234567 o +573009876543 o 301-456-7890\n"
            "Sitio web: https://www.ejemplo.com/pagina y http://portal.gov.co\n"
            "Fecha de entrega: 25/12/2024 o 2024-06-15\n"
            "Placa del vehículo: ABC123 y moto: XYZ45T\n"
            "Usuario: john_doe  Clave: Mi$Clave2024\n"
            "Email inválido: usuario@  Teléfono inválido: 1234\n"
        )
        self._text_input.insert("1.0", example)

    def _open_file(self) -> None:
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de texto",
            filetypes=[("Archivos de texto", "*.txt"), ("Todos", "*.*")],
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read()
            self._text_input.delete("1.0", tk.END)
            self._text_input.insert("1.0", content)
            self._current_file = path
            self._status_var.set(f"Archivo cargado: {path}")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo abrir el archivo:\n{exc}")

    def _analyze(self) -> None:
        text = self._text_input.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Sin texto", "Escribe o carga un texto para analizar.")
            return

        self._status_var.set("Analizando...")
        self.update_idletasks()

        if self._mode_var.get() == "word":
            tokens = self._lexer.tokenize_word_boundary(text)
        else:
            tokens = self._lexer.tokenize(text)

        self._tokens = tokens
        self._result_panel.display(tokens)

        # Registrar en historial
        for tok in tokens:
            self._history.add(
                value=tok.value,
                token_type=tok.type.label(),
                is_valid=tok.is_valid,
                errors=tok.details.get("errors", []),
                input_type="TEXT",
            )

        # Resaltar en el texto
        self._highlight_tokens(text, tokens)

        stats = self._lexer.stats
        self._status_var.set(
            f"Análisis completo — {stats.total_tokens} tokens "
            f"({stats.valid_tokens} válidos, {stats.invalid_tokens} inválidos)"
        )

    def _highlight_tokens(self, text: str, tokens: List[Token]) -> None:
        self._text_input.tag_remove("highlight", "1.0", tk.END)
        for tok in tokens:
            # Convertir offset a índice tkinter "línea.columna"
            start_idx = f"1.0 + {tok.start} chars"
            end_idx   = f"1.0 + {tok.end} chars"
            try:
                self._text_input.tag_add("highlight", start_idx, end_idx)
            except tk.TclError:
                pass

    def _clear(self) -> None:
        self._text_input.delete("1.0", tk.END)
        self._result_panel.clear()
        self._tokens = []
        self._status_var.set("Listo.")

    def _export(self, fmt: str) -> None:
        if not self._tokens:
            messagebox.showwarning("Sin datos", "Primero analiza un texto.")
            return

        ext_map = {"txt": "*.txt", "csv": "*.csv", "json": "*.json"}
        path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(fmt.upper(), ext_map[fmt]), ("Todos", "*.*")],
            title=f"Exportar como {fmt.upper()}",
        )
        if not path:
            return

        text = self._text_input.get("1.0", tk.END).strip()
        try:
            if fmt == "txt":
                Exporter.to_txt(self._tokens, path, source_text=text)
            elif fmt == "csv":
                Exporter.to_csv(self._tokens, path)
            elif fmt == "json":
                Exporter.to_json(self._tokens, path)
            messagebox.showinfo("Exportado", f"Archivo guardado en:\n{path}")
        except Exception as exc:
            messagebox.showerror("Error", f"No se pudo exportar:\n{exc}")
