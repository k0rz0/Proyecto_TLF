"""
Pestaña 3 — Simulador Visual de Autómatas Finitos Deterministas.

Funcionalidades:
- Catálogo de 9 AFDs (5 de validadores + 4 teóricos clásicos)
- Tabla de transiciones δ con marcadores → (inicial) y ★ (aceptación)
- Visualización gráfica del AFD en Canvas (estados + flechas + self-loops)
- Definición formal M = (Q, Σ, δ, q0, F) en el panel de información
- Simulación paso a paso y completa con resaltado animado del estado activo
- Traza textual de la forma: δ(qi, 'a' [CLASE]) → qj
"""

from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional, Tuple

from automata.dfa import DFA, DEAD_STATE, TransitionStep
from validators.email_validator import EmailValidator
from validators.phone_validator import PhoneValidator
from validators.date_validator import DateValidator
from validators.url_validator import UrlValidator
from validators.plate_validator import PlateValidator


# ---------------------------------------------------------------------------
# AFDs teóricos clásicos
# ---------------------------------------------------------------------------

def _make_binary_div3() -> DFA:
    """AFD que acepta binarios cuyo valor (base 10) es divisible por 3."""
    def classify(c: str) -> str:
        return c if c in ("0", "1") else "ELSE"

    return DFA(
        states={"q0", "q1", "q2"},
        alphabet={"0", "1", "ELSE"},
        transitions={
            "q0": {"0": "q0", "1": "q1"},
            "q1": {"0": "q2", "1": "q0"},
            "q2": {"0": "q1", "1": "q2"},
        },
        initial_state="q0",
        accept_states={"q0"},
        char_classifier=classify,
        name="Binario divisible por 3",
        description=(
            "Acepta cadenas binarias cuyo valor numérico es divisible por 3.\n"
            "El estado qi representa el residuo i al dividir por 3.\n"
            "La cadena vacía tiene valor 0 → aceptada (q0 es inicial y de aceptación).\n"
            "Basado en el Teorema de Myhill-Nerode: clases de equivalencia = residuos."
        ),
        regex_theory="(0 | 1(01*0)*1)*",
    )


def _make_binary_ends0() -> DFA:
    """
    AFD que acepta cadenas binarias NO VACÍAS que terminan en '0'.

    FIX C5: Se agrega un estado inicial no-aceptador (q_start) para que
    la cadena vacía ε sea correctamente rechazada.
    El docstring decía 'no vacías' pero el autómata anterior aceptaba ε.
    """
    def classify(c: str) -> str:
        return c if c in ("0", "1") else "ELSE"

    return DFA(
        states={"q_start", "q_par", "q_impar"},
        alphabet={"0", "1", "ELSE"},
        transitions={
            # q_start: estado inicial sin aceptación → rechaza ε
            "q_start": {"0": "q_par",   "1": "q_impar"},
            # q_par: terminó en '0'   → aceptación
            "q_par":   {"0": "q_par",   "1": "q_impar"},
            # q_impar: terminó en '1' → no aceptación
            "q_impar": {"0": "q_par",   "1": "q_impar"},
        },
        initial_state="q_start",
        accept_states={"q_par"},
        char_classifier=classify,
        name="Binario termina en '0'",
        description=(
            "Acepta cadenas binarias NO VACÍAS que terminan en el dígito 0.\n"
            "q_start: inicial (no acepta ε)\n"
            "q_par:   último dígito fue '0' → aceptación\n"
            "q_impar: último dígito fue '1' → no aceptación\n"
            "Corrección: se separó el estado inicial del de aceptación."
        ),
        regex_theory="(0|1)*0",
    )


def _make_identifier_dfa() -> DFA:
    """
    AFD para identificadores simples: [a-z][a-z0-9_]*

    Ejemplo canónico de análisis léxico — reconoce identificadores de
    lenguajes de programación que empiezan con letra minúscula.
    """
    def classify(c: str) -> str:
        if "a" <= c <= "z":
            return "LOWER"
        if c.isdigit():
            return "DIGIT"
        if c == "_":
            return "UNDER"
        return "ELSE"

    return DFA(
        states={"q0", "q1"},
        alphabet={"LOWER", "DIGIT", "UNDER", "ELSE"},
        transitions={
            "q0": {"LOWER": "q1"},
            "q1": {"LOWER": "q1", "DIGIT": "q1", "UNDER": "q1"},
        },
        initial_state="q0",
        accept_states={"q1"},
        char_classifier=classify,
        name="Identificadores [a-z][a-z0-9_]*",
        description=(
            "Reconoce identificadores que comienzan con letra minúscula\n"
            "seguida de letras, dígitos o guión bajo.\n"
            "q0: estado inicial (espera primera letra)\n"
            "q1: leyendo el cuerpo del identificador (aceptación)\n"
            "Ejemplo de uso en análisis léxico de compiladores."
        ),
        regex_theory="[a-z][a-z0-9_]*",
    )


def _make_decimal_dfa() -> DFA:
    """
    AFD para números decimales: [0-9]+(\\.[0-9]+)?

    Acepta enteros y reales; no acepta cadenas que terminen en punto.
    """
    def classify(c: str) -> str:
        if c.isdigit():
            return "DIGIT"
        if c == ".":
            return "DOT"
        return "ELSE"

    return DFA(
        states={"q0", "q1", "q2", "q3"},
        alphabet={"DIGIT", "DOT", "ELSE"},
        transitions={
            "q0": {"DIGIT": "q1"},
            "q1": {"DIGIT": "q1", "DOT": "q2"},  # ★ acepta enteros
            "q2": {"DIGIT": "q3"},                # después del punto, exige dígito
            "q3": {"DIGIT": "q3"},                # ★ acepta decimales
        },
        initial_state="q0",
        accept_states={"q1", "q3"},
        char_classifier=classify,
        name="Números decimales [0-9]+(.[0-9]+)?",
        description=(
            "Reconoce números enteros y decimales.\n"
            "q0: inicio\n"
            "q1: leyendo dígitos enteros (aceptación)\n"
            "q2: se leyó el punto — espera dígito decimal\n"
            "q3: leyendo decimales (aceptación)\n"
            "Nota: cadenas que terminan en '.' son rechazadas."
        ),
        regex_theory="[0-9]+(\\.[0-9]+)?",
    )


# ---------------------------------------------------------------------------
# Catálogo de AFDs
# ---------------------------------------------------------------------------

def _build_catalog() -> Dict[str, DFA]:
    """
    Construye el catálogo de AFDs disponibles en el simulador.

    FIX I2: usa la propiedad pública `.dfa` en lugar del método privado
    `._build_dfa()`, respetando el principio de encapsulamiento.
    """
    entries = [
        # Validadores del proyecto
        ("Email",                    lambda: EmailValidator().dfa),
        ("Teléfono",                 lambda: PhoneValidator().dfa),
        ("Fecha",                    lambda: DateValidator().dfa),
        ("URL",                      lambda: UrlValidator().dfa),
        ("Placa vehicular",          lambda: PlateValidator().dfa),
        # AFDs teóricos clásicos
        ("Binario divisible÷3",      _make_binary_div3),
        ("Binario termina en '0'",   _make_binary_ends0),
        ("Identificadores",          _make_identifier_dfa),
        ("Números decimales",        _make_decimal_dfa),
    ]
    catalog: Dict[str, DFA] = {}
    for name, builder in entries:
        try:
            catalog[name] = builder()
        except Exception:
            pass
    return catalog


# ---------------------------------------------------------------------------
# Constantes de dibujo
# ---------------------------------------------------------------------------

_R       = 28    # radio de los estados en px
_FONT_S  = ("Courier New", 9)
_FONT_M  = ("Courier New", 10, "bold")

_COLOR_DEFAULT  = "#90CAF9"   # azul claro  → estado normal
_COLOR_INITIAL  = "#A5D6A7"   # verde claro → estado inicial
_COLOR_ACCEPT   = "#FFF176"   # amarillo    → estado de aceptación
_COLOR_ACTIVE   = "#FF8A65"   # naranja     → estado activo (simulación)
_COLOR_DEAD_ACT = "#EF9A9A"   # rojo suave  → estado trampa activo


# ---------------------------------------------------------------------------
# Canvas de visualización del AFD
# ---------------------------------------------------------------------------

class DFACanvas(tk.Canvas):
    """
    Canvas que dibuja el grafo del AFD:
      • Círculos para estados (dobles para aceptación)
      • Flecha entrante para el estado inicial
      • Flechas etiquetadas entre estados (curvas si hay arco inverso)
      • Self-loops para transiciones reflexivas
      • Coloreado dinámico del estado activo durante la simulación
    """

    def __init__(self, master: tk.Widget, **kwargs) -> None:
        super().__init__(master, bg="#FAFAFA", **kwargs)
        self._dfa: Optional[DFA] = None
        self._positions: Dict[str, Tuple[float, float]] = {}
        self._state_items: Dict[str, int] = {}
        self._active: Optional[str] = None

    def load_dfa(self, dfa: DFA) -> None:
        self._dfa = dfa
        self._active = None
        self._draw()

    def highlight(self, state: str) -> None:
        self._active = state
        self._redraw_states()

    # ------------------------------------------------------------------

    def _draw(self) -> None:
        self.delete("all")
        if self._dfa is None:
            return
        self._compute_positions()
        self._draw_transitions()
        self._draw_states()

    def _compute_positions(self) -> None:
        states = sorted(s for s in self._dfa.states if s != DEAD_STATE)
        n = len(states)
        if not n:
            return

        w = int(self.winfo_width())  or 480
        h = int(self.winfo_height()) or 340
        cx, cy = w / 2, h / 2

        if n == 1:
            self._positions = {states[0]: (cx, cy)}
            return

        rx = min(cx - _R - 24, 200)
        ry = min(cy - _R - 24, 145)
        self._positions = {}
        for i, s in enumerate(states):
            angle = (2 * math.pi * i / n) - math.pi / 2
            self._positions[s] = (
                cx + rx * math.cos(angle),
                cy + ry * math.sin(angle),
            )

    def _draw_transitions(self) -> None:
        edge_labels: Dict[Tuple[str, str], List[str]] = {}
        for state, syms in self._dfa.transitions.items():
            if state == DEAD_STATE:
                continue
            for sym, nxt in syms.items():
                if nxt == DEAD_STATE:
                    continue
                key = (state, nxt)
                edge_labels.setdefault(key, [])
                if sym not in edge_labels[key]:
                    edge_labels[key].append(sym)

        for (frm, to), labels in edge_labels.items():
            # Agrupar etiquetas largas en varias líneas si hay muchas
            label_str = _format_label(sorted(labels))
            if frm == to:
                self._draw_self_loop(frm, label_str)
            else:
                curved = (to, frm) in edge_labels
                self._draw_arrow(frm, to, label_str, curved=curved)

    def _draw_arrow(self, frm: str, to: str, label: str, curved: bool = False) -> None:
        if frm not in self._positions or to not in self._positions:
            return
        x1, y1 = self._positions[frm]
        x2, y2 = self._positions[to]
        dist = math.hypot(x2 - x1, y2 - y1)
        if dist < 1:
            return
        nx, ny = (x2 - x1) / dist, (y2 - y1) / dist
        sx, sy = x1 + nx * _R, y1 + ny * _R
        ex, ey = x2 - nx * _R, y2 - ny * _R

        if curved:
            px, py = -ny * 32, nx * 32
            mx, my = (sx + ex) / 2 + px, (sy + ey) / 2 + py
            self.create_line(
                sx, sy, mx, my, ex, ey,
                smooth=True, arrow=tk.LAST, arrowshape=(10, 12, 4),
                width=2, fill="#455A64",
            )
            lx, ly = mx, my
        else:
            self.create_line(
                sx, sy, ex, ey,
                arrow=tk.LAST, arrowshape=(10, 12, 4),
                width=2, fill="#455A64",
            )
            lx, ly = (sx + ex) / 2, (sy + ey) / 2 - 8

        self.create_text(lx, ly, text=label, font=_FONT_S, fill="#C62828")

    def _draw_self_loop(self, state: str, label: str) -> None:
        if state not in self._positions:
            return
        x, y = self._positions[state]
        r2 = _R * 1.4
        self.create_oval(
            x - r2 / 2, y - _R - r2,
            x + r2 / 2, y - _R,
            outline="#455A64", width=2,
        )
        self.create_text(x, y - _R - r2 - 8, text=label, font=_FONT_S, fill="#C62828")

    def _draw_states(self) -> None:
        self._state_items = {}
        dfa = self._dfa
        for state, (x, y) in self._positions.items():
            # Doble círculo para estado de aceptación
            if state in dfa.accept_states:
                self.create_oval(
                    x - _R - 5, y - _R - 5, x + _R + 5, y + _R + 5,
                    outline="#1565C0", width=2,
                )
            # Círculo principal
            oid = self.create_oval(
                x - _R, y - _R, x + _R, y + _R,
                fill=self._state_color(state),
                outline="#1565C0", width=2,
            )
            self._state_items[state] = oid
            self.create_text(x, y, text=state, font=_FONT_M, fill="#1A237E")

            # Flecha del estado inicial
            if state == dfa.initial_state:
                self.create_line(
                    x - _R - 32, y, x - _R - 2, y,
                    arrow=tk.LAST, arrowshape=(10, 12, 4),
                    width=2, fill="#2E7D32",
                )

    def _redraw_states(self) -> None:
        if not self._dfa:
            return
        for state, oid in self._state_items.items():
            self.itemconfig(oid, fill=self._state_color(state))

    def _state_color(self, state: str) -> str:
        if state == self._active:
            return _COLOR_DEAD_ACT if state == DEAD_STATE else _COLOR_ACTIVE
        if self._dfa and state in self._dfa.accept_states:
            return _COLOR_ACCEPT
        if self._dfa and state == self._dfa.initial_state:
            return _COLOR_INITIAL
        return _COLOR_DEFAULT


# ---------------------------------------------------------------------------
# Pestaña completa
# ---------------------------------------------------------------------------

class AutomataTab(ttk.Frame):
    """Pestaña del Simulador AFD."""

    def __init__(self, master: tk.Widget, **kwargs) -> None:
        super().__init__(master, **kwargs)
        self._catalog  = _build_catalog()
        self._dfa: Optional[DFA] = None
        self._trace: List[TransitionStep] = []
        self._step_idx = 0
        self._build_ui()

    # ------------------------------------------------------------------
    # Construcción de la UI
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        # ── Barra de control ──────────────────────────────────────────
        top = ttk.Frame(self)
        top.pack(fill=tk.X, padx=6, pady=4)

        ttk.Label(top, text="AFD:", font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT)
        self._dfa_var = tk.StringVar()
        names = list(self._catalog.keys())
        self._dfa_combo = ttk.Combobox(
            top, textvariable=self._dfa_var, values=names,
            state="readonly", width=30,
        )
        self._dfa_combo.pack(side=tk.LEFT, padx=6)
        if names:
            self._dfa_combo.set(names[0])
        self._dfa_combo.bind("<<ComboboxSelected>>", self._load_dfa)

        ttk.Separator(top, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=8, pady=2)
        ttk.Label(top, text="Cadena de entrada:").pack(side=tk.LEFT)
        self._input_var = tk.StringVar()
        ttk.Entry(top, textvariable=self._input_var, width=30,
                  font=("Consolas", 11)).pack(side=tk.LEFT, padx=4)

        ttk.Button(top, text="▶ Ejecutar todo",
                   command=self._run_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="⏭ Paso a paso",
                   command=self._run_step).pack(side=tk.LEFT, padx=2)
        ttk.Button(top, text="↺ Reiniciar",
                   command=self._reset_sim).pack(side=tk.LEFT, padx=2)

        # ── Área principal: canvas | tabla + traza ────────────────────
        mid = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        mid.pack(fill=tk.BOTH, expand=True, padx=6, pady=2)

        # Canvas del grafo
        graph_frame = ttk.LabelFrame(mid, text="Grafo del AFD")
        mid.add(graph_frame, weight=3)

        self._canvas = DFACanvas(graph_frame, width=480, height=340)
        self._canvas.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self._canvas.bind("<Configure>", lambda _: self._redraw_canvas())

        # Panel derecho
        right = ttk.Frame(mid)
        mid.add(right, weight=2)

        tbl_frame = ttk.LabelFrame(right, text="Tabla de Transiciones δ")
        tbl_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 4))

        self._tbl_text = tk.Text(
            tbl_frame, height=11, font=("Courier New", 9),
            bg="#ECEFF1", state=tk.DISABLED,
        )
        sb_tbl = ttk.Scrollbar(tbl_frame, orient=tk.HORIZONTAL,
                                command=self._tbl_text.xview)
        sb_tbl_y = ttk.Scrollbar(tbl_frame, command=self._tbl_text.yview)
        self._tbl_text.configure(yscrollcommand=sb_tbl_y.set,
                                  xscrollcommand=sb_tbl.set)
        self._tbl_text.grid(row=0, column=0, sticky="nsew")
        sb_tbl_y.grid(row=0, column=1, sticky="ns")
        sb_tbl.grid(row=1, column=0, sticky="ew")
        tbl_frame.rowconfigure(0, weight=1)
        tbl_frame.columnconfigure(0, weight=1)

        trace_frame = ttk.LabelFrame(right, text="Traza δ(q, a) → q'")
        trace_frame.pack(fill=tk.BOTH, expand=True)

        self._trace_text = tk.Text(
            trace_frame, height=10, font=("Courier New", 9),
            bg="#1E1E1E", fg="#D4D4D4", state=tk.DISABLED,
        )
        sb_tr = ttk.Scrollbar(trace_frame, command=self._trace_text.yview)
        self._trace_text.configure(yscrollcommand=sb_tr.set)
        self._trace_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_tr.pack(side=tk.RIGHT, fill=tk.Y)

        # ── Panel de información formal ────────────────────────────────
        bottom = ttk.Frame(self)
        bottom.pack(fill=tk.X, padx=6, pady=2)

        self._info_lbl = ttk.Label(
            bottom, text="Selecciona un AFD para comenzar.",
            font=("Segoe UI", 9), wraplength=820,
        )
        self._info_lbl.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self._result_lbl = tk.Label(
            bottom, text="", font=("Segoe UI", 12, "bold"), width=16,
        )
        self._result_lbl.pack(side=tk.RIGHT, padx=8)
        self._result_lbl_default_bg = self._result_lbl.cget("bg")

        # Cargar primer AFD
        if names:
            self._load_dfa()

    # ------------------------------------------------------------------
    # Carga de AFD
    # ------------------------------------------------------------------

    def _load_dfa(self, _event=None) -> None:
        name = self._dfa_var.get()
        if name not in self._catalog:
            return
        self._dfa = self._catalog[name]
        self._reset_sim()
        self._update_table()
        self._redraw_canvas()

        # Mostrar definición formal M = (Q, Σ, δ, q0, F)
        dfa = self._dfa
        q_list  = sorted(s for s in dfa.states if s != DEAD_STATE)
        sigma   = sorted(dfa.alphabet)
        self._info_lbl.config(
            text=(
                f"M = (Q, Σ, δ, q0, F)   "
                f"Q={{{', '.join(q_list[:6])}{',...' if len(q_list)>6 else ''}}}   "
                f"Σ={{{', '.join(sigma[:5])}{',...' if len(sigma)>5 else ''}}}   "
                f"q0={dfa.initial_state}   F={{{', '.join(dfa.accept_states)}}}\n"
                f"ER teórica: {dfa.regex_theory}   |   {dfa.description.split(chr(10))[0]}"
            )
        )

    def _redraw_canvas(self) -> None:
        if self._dfa:
            self._canvas.load_dfa(self._dfa)

    def _update_table(self) -> None:
        if self._dfa is None:
            return
        tbl     = self._dfa.get_transition_table()
        states  = tbl["states"]
        alphabet = tbl["alphabet"]
        initial = tbl["initial"]
        accept  = set(tbl["accept"])

        col_w = 10
        header = f"{'Estado':>{col_w}} │ " + " │ ".join(
            f"{s:>{col_w}}" for s in alphabet
        )
        sep = "─" * len(header)
        lines = [sep, header, sep]

        for row in tbl["rows"]:
            st = row["state"]
            if   st == initial and st in accept:
                marker = "→★"
            elif st == initial:
                marker = "→ "
            elif st in accept:
                marker = "★ "
            else:
                marker = "  "
            state_label = f"{marker}{st}"
            cells = " │ ".join(
                f"{row['transitions'].get(s, '—'):>{col_w}}" for s in alphabet
            )
            lines.append(f"{state_label:>{col_w}} │ {cells}")

        lines += [sep, "→ = estado inicial   ★ = estado de aceptación   — = estado trampa"]

        self._tbl_text.configure(state=tk.NORMAL)
        self._tbl_text.delete("1.0", tk.END)
        self._tbl_text.insert("1.0", "\n".join(lines))
        self._tbl_text.configure(state=tk.DISABLED)

    # ------------------------------------------------------------------
    # Simulación
    # ------------------------------------------------------------------

    def _run_all(self) -> None:
        if self._dfa is None:
            messagebox.showinfo("Sin AFD", "Carga un AFD primero.")
            return
        string = self._input_var.get()
        accepted, trace = self._dfa.process_with_trace(string)
        self._trace    = trace
        self._step_idx = len(trace)
        self._show_trace_all(string)
        final = trace[-1].to_state if trace else self._dfa.initial_state
        self._canvas.highlight(final)
        self._show_result(accepted)

    def _run_step(self) -> None:
        if self._dfa is None:
            messagebox.showinfo("Sin AFD", "Carga un AFD primero.")
            return

        if self._step_idx == 0:
            string = self._input_var.get()
            _, self._trace = self._dfa.process_with_trace(string)
            self._show_trace_header(string)

        if self._step_idx >= len(self._trace):
            messagebox.showinfo("Fin", "Simulación terminada. Presiona ↺ para reiniciar.")
            return

        step = self._trace[self._step_idx]
        self._step_idx += 1
        self._canvas.highlight(step.to_state)
        self._append_trace_line(step.to_str())

        if self._step_idx >= len(self._trace):
            final    = self._trace[-1].to_state
            accepted = (final in self._dfa.accept_states) and (final != DEAD_STATE)
            self._show_result(accepted)

    def _reset_sim(self) -> None:
        self._trace    = []
        self._step_idx = 0
        if self._dfa:
            self._dfa.reset()
        self._canvas.highlight("")
        self._trace_text.configure(state=tk.NORMAL)
        self._trace_text.delete("1.0", tk.END)
        self._trace_text.configure(state=tk.DISABLED)
        self._result_lbl.config(text="", bg=self._result_lbl_default_bg)

    # ------------------------------------------------------------------
    # Helpers de traza
    # ------------------------------------------------------------------

    def _show_trace_header(self, string: str) -> None:
        self._trace_text.configure(state=tk.NORMAL)
        self._trace_text.delete("1.0", tk.END)
        self._trace_text.insert(
            tk.END,
            f"AFD:    {self._dfa.name}\n"
            f"Cadena: '{string}'\n"
            + "─" * 52 + "\n"
        )
        self._trace_text.configure(state=tk.DISABLED)

    def _show_trace_all(self, string: str) -> None:
        self._trace_text.configure(state=tk.NORMAL)
        self._trace_text.delete("1.0", tk.END)
        self._trace_text.insert(
            tk.END,
            f"AFD:    {self._dfa.name}\n"
            f"Cadena: '{string}'\n"
            + "─" * 52 + "\n"
        )
        for step in self._trace:
            self._trace_text.insert(tk.END, step.to_str() + "\n")
        self._trace_text.see(tk.END)
        self._trace_text.configure(state=tk.DISABLED)

    def _append_trace_line(self, line: str) -> None:
        self._trace_text.configure(state=tk.NORMAL)
        self._trace_text.insert(tk.END, line + "\n")
        self._trace_text.see(tk.END)
        self._trace_text.configure(state=tk.DISABLED)

    def _show_result(self, accepted: bool) -> None:
        if accepted:
            self._result_lbl.config(text="✓ ACEPTADA", fg="white", bg="#2E7D32")
        else:
            self._result_lbl.config(text="✗ RECHAZADA", fg="white", bg="#C62828")
        self._append_trace_line(
            "─" * 52 + "\n"
            + ("  ACEPTADA ✓" if accepted else "  RECHAZADA ✗")
        )


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _format_label(symbols: List[str]) -> str:
    """
    Formatea la lista de símbolos de una arista.
    Agrupa en varias líneas si hay más de 3 símbolos.
    """
    if len(symbols) <= 3:
        return ",".join(symbols)
    # Agrupar en líneas de 3
    lines = []
    for i in range(0, len(symbols), 3):
        lines.append(",".join(symbols[i:i + 3]))
    return "\n".join(lines)
