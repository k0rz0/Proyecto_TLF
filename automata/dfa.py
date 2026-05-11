"""
Autómata Finito Determinista (AFD) — Implementación base.

Definición formal: M = (Q, Σ, δ, q0, F) donde
    Q  : conjunto finito de estados
    Σ  : alfabeto de clases de caracteres
    δ  : función de transición  Q × Σ → Q
    q0 : estado inicial
    F  : conjunto de estados de aceptación (F ⊆ Q)

La función δ opera sobre *clases* de caracteres (ej. ALPHA, DIGIT) en
lugar de caracteres individuales, lo que permite construir autómatas
generales sin necesitar un arco por cada símbolo del alfabeto ASCII.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

# Centinela para el estado trampa (dead / sink state)
DEAD_STATE = "__DEAD__"


# ---------------------------------------------------------------------------
# Estructura de datos para un paso de simulación
# ---------------------------------------------------------------------------

@dataclass
class TransitionStep:
    """Registro detallado de un paso de la simulación del AFD."""

    step: int
    char: Optional[str]          # carácter leído (None → estado inicial)
    symbol_class: Optional[str]  # clase a la que pertenece el carácter
    from_state: Optional[str]    # estado de origen
    to_state: str                # estado destino
    is_dead: bool = False        # True si se llegó al estado trampa
    is_accept: bool = False      # True si to_state ∈ F

    def to_str(self) -> str:
        if self.char is None:
            marker = "✓ ACEPTA" if self.is_accept else ""
            return f"  → Estado inicial: {self.to_state}  {marker}"
        suffix = ""
        if self.is_dead:
            suffix = "  ✗ MUERTO"
        elif self.is_accept:
            suffix = "  ✓ ACEPTA"
        return (
            f"  Paso {self.step:>2}: δ({self.from_state}, '{self.char}'"
            f" [{self.symbol_class}]) → {self.to_state}{suffix}"
        )


# ---------------------------------------------------------------------------
# Clase principal DFA
# ---------------------------------------------------------------------------

class DFA:
    """
    Autómata Finito Determinista.

    Parámetros
    ----------
    states : Set[str]
        Conjunto Q de estados (no incluir DEAD_STATE; se agrega solo).
    alphabet : Set[str]
        Conjunto Σ de clases de caracteres usadas en las transiciones.
    transitions : Dict[str, Dict[str, str]]
        Tabla δ: {estado: {clase_símbolo: estado_destino}}.
        Las transiciones no definidas llevan implícitamente a DEAD_STATE.
    initial_state : str
        Estado inicial q0.
    accept_states : Set[str]
        Conjunto F de estados de aceptación.
    char_classifier : Callable[[str], str]
        Función que mapea un carácter a su clase de símbolo en Σ.
    name : str
        Nombre descriptivo del autómata.
    description : str
        Descripción académica (expresión regular teórica, etc.).
    """

    DEAD_STATE = DEAD_STATE

    def __init__(
        self,
        states: Set[str],
        alphabet: Set[str],
        transitions: Dict[str, Dict[str, str]],
        initial_state: str,
        accept_states: Set[str],
        char_classifier: Callable[[str], str],
        name: str = "AFD",
        description: str = "",
        regex_theory: str = "",
    ) -> None:
        self.states: Set[str] = states | {DEAD_STATE}
        self.alphabet: Set[str] = alphabet
        self.transitions: Dict[str, Dict[str, str]] = transitions
        self.initial_state: str = initial_state
        self.accept_states: Set[str] = accept_states
        self.char_classifier: Callable[[str], str] = char_classifier
        self.name: str = name
        self.description: str = description
        self.regex_theory: str = regex_theory  # ER teórica equivalente

        # Estado actual mutable (usado en proceso paso a paso externo)
        self._current_state: str = initial_state

    # ------------------------------------------------------------------
    # Propiedades
    # ------------------------------------------------------------------

    @property
    def current_state(self) -> str:
        return self._current_state

    # ------------------------------------------------------------------
    # Función de transición δ
    # ------------------------------------------------------------------

    def delta(self, state: str, symbol: str) -> str:
        """δ(q, a) → q'  —  retorna DEAD_STATE si la transición no existe."""
        if state == DEAD_STATE:
            return DEAD_STATE
        return self.transitions.get(state, {}).get(symbol, DEAD_STATE)

    def classify_char(self, char: str) -> str:
        """Clasifica un carácter en su clase de símbolo."""
        return self.char_classifier(char)

    # ------------------------------------------------------------------
    # Procesamiento de cadenas
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reinicia el autómata al estado inicial q0."""
        self._current_state = self.initial_state

    def process(self, string: str) -> bool:
        """
        Procesa la cadena completa y retorna True si es aceptada.

        Complejidad: O(|string|)
        """
        self.reset()
        for char in string:
            symbol = self.classify_char(char)
            self._current_state = self.delta(self._current_state, symbol)
            if self._current_state == DEAD_STATE:
                return False
        return self._current_state in self.accept_states

    def process_with_trace(
        self, string: str
    ) -> Tuple[bool, List[TransitionStep]]:
        """
        Procesa la cadena y retorna (aceptada, traza completa).

        La traza incluye el estado inicial (paso 0) y un registro por
        cada carácter leído. Se usa en el módulo Simulador AFD.
        """
        self.reset()
        state = self.initial_state
        trace: List[TransitionStep] = []

        # Paso 0: estado inicial
        trace.append(
            TransitionStep(
                step=0,
                char=None,
                symbol_class=None,
                from_state=None,
                to_state=state,
                is_accept=state in self.accept_states,
            )
        )

        for i, char in enumerate(string, start=1):
            symbol = self.classify_char(char)
            from_state = state
            to_state = self.delta(state, symbol)
            state = to_state

            trace.append(
                TransitionStep(
                    step=i,
                    char=char,
                    symbol_class=symbol,
                    from_state=from_state,
                    to_state=to_state,
                    is_dead=(to_state == DEAD_STATE),
                    is_accept=(to_state in self.accept_states),
                )
            )

            if to_state == DEAD_STATE:
                break

        accepted = state in self.accept_states
        return accepted, trace

    def find_longest_match(self, text: str, start: int) -> int:
        """
        Busca el final de la coincidencia más larga que comienza en `start`.

        Retorna el índice de fin (exclusivo) de la mejor coincidencia,
        o `start` si no hay ninguna. Usado por el Lexer.
        """
        self.reset()
        last_accept_end = -1
        state = self.initial_state

        for i in range(start, len(text)):
            symbol = self.classify_char(text[i])
            state = self.delta(state, symbol)
            if state == DEAD_STATE:
                break
            if state in self.accept_states:
                last_accept_end = i + 1

        return last_accept_end if last_accept_end > start else start

    # ------------------------------------------------------------------
    # Tabla de transiciones para visualización
    # ------------------------------------------------------------------

    def get_transition_table(self) -> Dict:
        """
        Genera la tabla de transiciones para mostrar en la GUI.

        Retorna un diccionario con claves:
            states   : lista ordenada de estados (sin DEAD_STATE)
            alphabet : lista ordenada de símbolos
            initial  : estado inicial
            accept   : lista de estados de aceptación
            rows     : [{"state": str, "transitions": {sym: str}}]
        """
        sorted_states = sorted(s for s in self.states if s != DEAD_STATE)
        sorted_syms = sorted(self.alphabet)

        rows = []
        for st in sorted_states:
            row: Dict = {"state": st, "transitions": {}}
            for sym in sorted_syms:
                nxt = self.delta(st, sym)
                row["transitions"][sym] = nxt if nxt != DEAD_STATE else "—"
            rows.append(row)

        return {
            "states": sorted_states,
            "alphabet": sorted_syms,
            "initial": self.initial_state,
            "accept": list(self.accept_states),
            "rows": rows,
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"DFA(name={self.name!r}, states={len(self.states)-1}, "
            f"accept={self.accept_states})"
        )
