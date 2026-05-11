"""
Panel de resultados reutilizable: tabla de tokens + árbol sintáctico.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import List, Optional

from lexical.token_types import Token, TokenType


_COL_CONFIG = [
    ("N°",       50,  "center"),
    ("Tipo",     100, "center"),
    ("Valor",    200, "w"),
    ("Posición", 110, "center"),
    ("Longitud", 70,  "center"),
    ("L:C",      80,  "center"),
    ("Estado",   80,  "center"),
]

_TAG_VALID   = "valid"
_TAG_INVALID = "invalid"


class ResultPanel(ttk.Frame):
    """
    Frame que muestra:
    - Una tabla (Treeview) con todos los tokens encontrados.
    - Un cuadro de texto con el árbol sintáctico del token seleccionado.
    - Un label de estadísticas rápidas.
    """

    def __init__(self, master: tk.Widget, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._tokens: List[Token] = []
        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Panel superior: tabla ──────────────────────────────────────
        table_frame = ttk.LabelFrame(self, text="Tokens Encontrados")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        cols = [c[0] for c in _COL_CONFIG]
        self._tree = ttk.Treeview(
            table_frame, columns=cols, show="headings", height=12
        )
        for col, width, anchor in _COL_CONFIG:
            self._tree.heading(col, text=col)
            self._tree.column(col, width=width, anchor=anchor, minwidth=40)

        sb_y = ttk.Scrollbar(table_frame, orient=tk.VERTICAL,   command=self._tree.yview)
        sb_x = ttk.Scrollbar(table_frame, orient=tk.HORIZONTAL, command=self._tree.xview)
        self._tree.configure(yscrollcommand=sb_y.set, xscrollcommand=sb_x.set)

        self._tree.grid(row=0, column=0, sticky="nsew")
        sb_y.grid(row=0, column=1, sticky="ns")
        sb_x.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        # Colores de filas
        self._tree.tag_configure(_TAG_VALID,   background="#E8F5E9", foreground="#1B5E20")
        self._tree.tag_configure(_TAG_INVALID, background="#FFEBEE", foreground="#B71C1C")

        # Evento selección
        self._tree.bind("<<TreeviewSelect>>", self._on_select)

        # ── Panel inferior: árbol sintáctico + estadísticas ────────────
        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))

        # Árbol sintáctico
        tree_frame = ttk.LabelFrame(bottom, text="Árbol Sintáctico")
        tree_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))

        self._tree_text = tk.Text(
            tree_frame, height=8, font=("Courier New", 10),
            bg="#1E1E1E", fg="#D4D4D4", wrap=tk.NONE
        )
        sb_tree = ttk.Scrollbar(tree_frame, command=self._tree_text.yview)
        self._tree_text.configure(yscrollcommand=sb_tree.set)
        self._tree_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_tree.pack(side=tk.RIGHT, fill=tk.Y)

        # Estadísticas
        stats_frame = ttk.LabelFrame(bottom, text="Estadísticas")
        stats_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 0))

        self._stats_text = tk.Text(
            stats_frame, width=22, height=8,
            font=("Courier New", 9), bg="#F5F5F5", state=tk.DISABLED
        )
        self._stats_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def display(self, tokens: List[Token]) -> None:
        """Carga y muestra la lista de tokens en la tabla."""
        self._tokens = tokens
        # Limpiar tabla
        for item in self._tree.get_children():
            self._tree.delete(item)

        counts: dict[str, int] = {}
        valid_count = 0
        invalid_count = 0

        for i, tok in enumerate(tokens, 1):
            tag = _TAG_VALID if tok.is_valid else _TAG_INVALID
            estado = "✓ Válido" if tok.is_valid else "✗ Inválido"
            self._tree.insert(
                "",
                tk.END,
                iid=str(i - 1),
                values=(
                    i,
                    tok.type.label(),
                    tok.value,
                    f"{tok.start}–{tok.end}",
                    tok.length,
                    f"L{tok.line}:C{tok.column}",
                    estado,
                ),
                tags=(tag,),
            )
            label = tok.type.label()
            counts[label] = counts.get(label, 0) + 1
            if tok.is_valid:
                valid_count += 1
            else:
                invalid_count += 1

        # Actualizar estadísticas
        lines = [
            f"Total: {len(tokens)}",
            f"  ✓ Válidos:   {valid_count}",
            f"  ✗ Inválidos: {invalid_count}",
            "",
            "Por tipo:",
        ]
        for k, v in sorted(counts.items()):
            lines.append(f"  {k}: {v}")

        self._stats_text.configure(state=tk.NORMAL)
        self._stats_text.delete("1.0", tk.END)
        self._stats_text.insert("1.0", "\n".join(lines))
        self._stats_text.configure(state=tk.DISABLED)

        # Limpiar árbol sintáctico
        self._tree_text.delete("1.0", tk.END)

    def clear(self) -> None:
        """Limpia todos los datos mostrados."""
        self.display([])
        self._tree_text.delete("1.0", tk.END)

    # ------------------------------------------------------------------
    # Eventos
    # ------------------------------------------------------------------

    def _on_select(self, _event=None) -> None:
        """Muestra el árbol sintáctico del token seleccionado."""
        sel = self._tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        if idx >= len(self._tokens):
            return
        tok = self._tokens[idx]
        self._show_syntax_tree(tok)

    def _show_syntax_tree(self, tok: Token) -> None:
        self._tree_text.delete("1.0", tk.END)

        tree_data = tok.details.get("syntax_tree", {})
        components = tok.details.get("components", {})
        errors = tok.details.get("errors", [])

        if tree_data:
            from syntax.syntax_tree import SyntaxTree
            tree = SyntaxTree.from_dict(tree_data)
            self._tree_text.insert(tk.END, tree.display() + "\n\n")

        if components:
            self._tree_text.insert(tk.END, "Componentes:\n")
            for k, v in components.items():
                self._tree_text.insert(tk.END, f"  {k}: {v}\n")

        if errors:
            self._tree_text.insert(tk.END, "\nErrores:\n")
            for e in errors:
                self._tree_text.insert(tk.END, f"  ✗ {e}\n")
