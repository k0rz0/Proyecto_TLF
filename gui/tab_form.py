"""
Pestaña 2 — Formulario Interactivo con Validación en Tiempo Real.

Cada campo usa su validador específico y actualiza el estado visual
mientras el usuario escribe (evento <KeyRelease>).

Colores de retroalimentación:
    Verde  (#E8F5E9) → válido
    Rojo   (#FFEBEE) → inválido / incompleto
    Gris   (#F5F5F5) → sin contenido aún
"""

from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Callable, Dict, Optional, Tuple

from lexical.token_types import TokenType
from utils.history import HistoryManager
from validators import (
    EmailValidator,
    PhoneValidator,
    DateValidator,
    UrlValidator,
    PasswordValidator,
    UsernameValidator,
)
from validators.base import BaseValidator, ValidationResult

_COLOR_OK      = "#E8F5E9"
_COLOR_ERR     = "#FFEBEE"
_COLOR_NEUTRAL = "#FFFFFF"
_FG_OK         = "#2E7D32"
_FG_ERR        = "#C62828"
_FG_NEUTRAL    = "#757575"


class FieldWidget:
    """Widget de campo de formulario con validación integrada."""

    def __init__(
        self,
        parent: tk.Widget,
        label: str,
        token_type: TokenType,
        validator: BaseValidator,
        row: int,
        show: str = "",
        placeholder: str = "",
    ) -> None:
        self.token_type  = token_type
        self.validator   = validator
        self.is_valid    = False
        self._last_value = ""
        self._result: Optional[ValidationResult] = None
        self._placeholder         = placeholder
        self._showing_placeholder = False

        # Label
        lbl = ttk.Label(parent, text=label, font=("Segoe UI", 10, "bold"))
        lbl.grid(row=row, column=0, sticky=tk.W, padx=(8, 4), pady=5)

        # Icono tipo token
        icon_lbl = ttk.Label(parent, text=token_type.label(),
                              foreground="#5C6BC0", font=("Segoe UI", 8))
        icon_lbl.grid(row=row, column=1, sticky=tk.W, padx=0)

        # Entry
        self._var = tk.StringVar()
        self._entry = tk.Entry(
            parent, textvariable=self._var, font=("Consolas", 11),
            show=show, width=35, bg=_COLOR_NEUTRAL
        )
        self._entry.grid(row=row, column=2, sticky=tk.EW, padx=4, pady=3)
        if placeholder:
            self._set_placeholder(placeholder)

        # Etiqueta de estado
        self._status_lbl = tk.Label(
            parent, text="", font=("Segoe UI", 9),
            fg=_FG_NEUTRAL, width=40, anchor=tk.W
        )
        self._status_lbl.grid(row=row, column=3, sticky=tk.W, padx=4)

        # Evento de validación en tiempo real
        self._var.trace_add("write", lambda *_: self._on_change())

    def _set_placeholder(self, text: str) -> None:
        # Flag must be True BEFORE insert so the trace callback ignores this write
        self._showing_placeholder = True
        self._entry.insert(0, text)
        self._entry.config(fg="gray")

        def on_focus_in(_e):
            if self._showing_placeholder:
                self._showing_placeholder = False
                self._entry.delete(0, tk.END)
                self._entry.config(fg="black")

        def on_focus_out(_e):
            if not self._entry.get():
                self._showing_placeholder = True
                self._entry.insert(0, text)
                self._entry.config(fg="gray")

        self._entry.bind("<FocusIn>",  on_focus_in)
        self._entry.bind("<FocusOut>", on_focus_out)

    def _on_change(self) -> None:
        if self._showing_placeholder:
            self._set_neutral()
            return
        value = self._var.get().strip()
        if not value:
            self._set_neutral()
            return
        self._result = self.validator.validate(value)
        self.is_valid = self._result.is_valid
        self._last_value = value
        if self.is_valid:
            self._set_ok()
        else:
            self._set_error()

    def _set_ok(self) -> None:
        self._entry.config(bg=_COLOR_OK)
        self._status_lbl.config(
            text="✓ Válido", fg=_FG_OK
        )

    def _set_error(self) -> None:
        self._entry.config(bg=_COLOR_ERR)
        msg = self._result.errors[0] if self._result and self._result.errors else "Inválido"
        self._status_lbl.config(text=f"✗ {msg}", fg=_FG_ERR)

    def _set_neutral(self) -> None:
        self._entry.config(bg=_COLOR_NEUTRAL)
        self._status_lbl.config(text="", fg=_FG_NEUTRAL)
        self.is_valid = False

    def get_value(self) -> str:
        if self._showing_placeholder:
            return ""
        return self._var.get().strip()

    def get_result(self) -> Optional[ValidationResult]:
        return self._result

    def reset(self) -> None:
        self._showing_placeholder = False
        self._var.set("")           # triggers _on_change → _set_neutral (empty)
        self._set_neutral()
        if self._placeholder:
            # Re-show placeholder without triggering validation
            self._showing_placeholder = True
            self._entry.insert(0, self._placeholder)   # triggers _on_change → _set_neutral
            self._entry.config(fg="gray")


class FormTab(ttk.Frame):
    """
    Pestaña de formulario interactivo con validación en tiempo real.
    """

    def __init__(self, master: tk.Widget, history: HistoryManager, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._history = history
        self._fields: Dict[str, FieldWidget] = {}
        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Título ─────────────────────────────────────────────────────
        ttk.Label(
            self,
            text="Formulario de Registro — Validación en Tiempo Real",
            font=("Segoe UI", 13, "bold"),
        ).pack(pady=10)

        # ── Frame con los campos ───────────────────────────────────────
        form_outer = ttk.Frame(self)
        form_outer.pack(fill=tk.BOTH, expand=True, padx=10)

        form_frame = ttk.LabelFrame(form_outer, text="Datos del usuario")
        form_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        form_frame.columnconfigure(2, weight=1)

        # Nombre (sin AFD especial, solo texto)
        self._nombre_var = tk.StringVar()
        ttk.Label(form_frame, text="Nombre completo",
                  font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, padx=8, pady=5
        )
        ttk.Label(form_frame, text="TEXTO", foreground="#5C6BC0",
                  font=("Segoe UI", 8)).grid(row=0, column=1, sticky=tk.W)
        self._nombre_entry = tk.Entry(
            form_frame, textvariable=self._nombre_var,
            font=("Consolas", 11), width=35
        )
        self._nombre_entry.grid(row=0, column=2, sticky=tk.EW, padx=4, pady=3)
        self._nombre_status = tk.Label(
            form_frame, text="", font=("Segoe UI", 9), width=40, anchor=tk.W
        )
        self._nombre_status.grid(row=0, column=3, sticky=tk.W, padx=4)
        self._nombre_var.trace_add("write", lambda *_: self._validate_nombre())

        # Campos con AFD
        field_defs = [
            ("Correo electrónico", "email",    TokenType.EMAIL,    EmailValidator(),    1, "", "usuario@dominio.com"),
            ("Teléfono",           "phone",    TokenType.PHONE,    PhoneValidator(),    2, "", "3001234567"),
            ("Fecha de nacimiento","date",     TokenType.DATE,     DateValidator(),     3, "", "DD/MM/YYYY"),
            ("Sitio web",          "url",      TokenType.URL,      UrlValidator(),      4, "", "https://"),
            ("Nombre de usuario",  "username", TokenType.USERNAME, UsernameValidator(), 5, "", "min 3 chars"),
            ("Contraseña",         "password", TokenType.PASSWORD, PasswordValidator(), 6, "*", ""),
        ]
        for label, key, ttype, validator, row, show, ph in field_defs:
            fw = FieldWidget(form_frame, label, ttype, validator, row, show=show, placeholder=ph)
            self._fields[key] = fw

        # ── Panel lateral: barra de fortaleza + árbol sintáctico ───────
        side_frame = ttk.Frame(form_outer)
        side_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(8, 4))

        # Barra de fortaleza de contraseña
        pwd_frame = ttk.LabelFrame(side_frame, text="Fortaleza de contraseña")
        pwd_frame.pack(fill=tk.X, pady=(0, 8))

        self._strength_bar = ttk.Progressbar(
            pwd_frame, maximum=5, mode="determinate", length=200
        )
        self._strength_bar.pack(padx=8, pady=4)
        self._strength_lbl = ttk.Label(pwd_frame, text="—", font=("Segoe UI", 9))
        self._strength_lbl.pack()

        # Hook al campo de contraseña para actualizar barra
        self._fields["password"]._var.trace_add("write", lambda *_: self._update_strength())

        # Árbol sintáctico del último campo validado
        tree_frame = ttk.LabelFrame(side_frame, text="Análisis Sintáctico")
        tree_frame.pack(fill=tk.BOTH, expand=True)

        self._syntax_text = tk.Text(
            tree_frame, width=35, height=18,
            font=("Courier New", 9), bg="#1E1E1E", fg="#D4D4D4"
        )
        self._syntax_text.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        # ── Botones de acción ──────────────────────────────────────────
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)

        self._submit_btn = ttk.Button(
            btn_frame, text="✅ Enviar formulario",
            command=self._submit, style="Accent.TButton"
        )
        self._submit_btn.pack(side=tk.LEFT, padx=10)

        ttk.Button(
            btn_frame, text="🔄 Limpiar todo",
            command=self._reset_all
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            btn_frame, text="🔬 Analizar campo",
            command=self._analyze_selected
        ).pack(side=tk.LEFT, padx=5)

        # Mensaje de estado global
        self._form_status = tk.Label(
            self, text="Complete todos los campos.", font=("Segoe UI", 10),
            fg=_FG_NEUTRAL
        )
        self._form_status.pack(pady=4)

        # Actualizar state del botón cada segundo
        self._check_form_state()

    # ------------------------------------------------------------------
    # Lógica de validación y UI
    # ------------------------------------------------------------------

    def _validate_nombre(self) -> None:
        val = self._nombre_var.get().strip()
        if len(val) >= 3:
            self._nombre_entry.config(bg=_COLOR_OK)
            self._nombre_status.config(text="✓ Válido", fg=_FG_OK)
        elif val:
            self._nombre_entry.config(bg=_COLOR_ERR)
            self._nombre_status.config(text="✗ Mínimo 3 caracteres", fg=_FG_ERR)
        else:
            self._nombre_entry.config(bg=_COLOR_NEUTRAL)
            self._nombre_status.config(text="", fg=_FG_NEUTRAL)

    def _update_strength(self) -> None:
        val = self._fields["password"].get_value()
        result = self._fields["password"].get_result()
        if not result:
            return
        score_map = {
            "Muy débil": 1, "Débil": 2, "Media": 3, "Fuerte": 4, "Muy fuerte": 5
        }
        strength = result.components.get("fortaleza", "Muy débil")
        score = score_map.get(strength, 1)
        self._strength_bar["value"] = score
        colors = ["#F44336", "#FF9800", "#FFC107", "#8BC34A", "#4CAF50"]
        self._strength_lbl.config(text=strength, foreground=colors[score - 1])

        # Actualizar árbol sintáctico
        self._show_syntax(result)

    def _show_syntax(self, result) -> None:
        self._syntax_text.delete("1.0", tk.END)
        if result.syntax_tree:
            from syntax.syntax_tree import SyntaxTree
            tree = SyntaxTree.from_dict(result.syntax_tree)
            self._syntax_text.insert(tk.END, tree.display())
        if result.components:
            self._syntax_text.insert(tk.END, "\n\nComponentes:\n")
            for k, v in result.components.items():
                self._syntax_text.insert(tk.END, f"  {k}: {v}\n")

    def _check_form_state(self) -> None:
        """Comprueba si el formulario es completamente válido."""
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return

        nombre_ok = len(self._nombre_var.get().strip()) >= 3
        fields_ok = all(fw.is_valid for fw in self._fields.values())
        all_ok = nombre_ok and fields_ok

        if all_ok:
            self._form_status.config(
                text="✅ Formulario listo para enviar", fg=_FG_OK
            )
        else:
            pending = sum(1 for fw in self._fields.values() if not fw.is_valid)
            if not nombre_ok:
                pending += 1
            self._form_status.config(
                text=f"⚠ Faltan {pending} campo(s) válido(s)", fg=_FG_ERR
            )

        self.after(500, self._check_form_state)

    def _analyze_selected(self) -> None:
        """Muestra el árbol sintáctico del primer campo con datos."""
        for fw in self._fields.values():
            if fw.get_value() and fw.get_result():
                self._show_syntax(fw.get_result())
                return

    def _submit(self) -> None:
        nombre_ok = len(self._nombre_var.get().strip()) >= 3
        fields_ok = all(fw.is_valid for fw in self._fields.values())

        if not (nombre_ok and fields_ok):
            messagebox.showwarning(
                "Formulario incompleto",
                "Por favor corrige los campos marcados en rojo antes de enviar."
            )
            return

        # Registrar en historial
        for key, fw in self._fields.items():
            result = fw.get_result()
            if result:
                self._history.add(
                    value=fw.get_value(),
                    token_type=fw.token_type.label(),
                    is_valid=result.is_valid,
                    errors=result.errors,
                    input_type="FORM",
                )

        messagebox.showinfo(
            "¡Formulario enviado!",
            f"Datos registrados correctamente.\n"
            f"Nombre: {self._nombre_var.get()}\n"
            f"Correo: {self._fields['email'].get_value()}"
        )

    def _reset_all(self) -> None:
        self._nombre_var.set("")
        for fw in self._fields.values():
            fw.reset()
        self._syntax_text.delete("1.0", tk.END)
        self._strength_bar["value"] = 0
        self._strength_lbl.config(text="—")
