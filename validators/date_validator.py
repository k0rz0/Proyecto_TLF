"""
Validador de fechas mediante AFD.

Formatos aceptados:
    F1: DD/MM/YYYY   → 25/12/2024
    F2: YYYY-MM-DD   → 2024-12-25

Expresión regular teórica:
    [0-9]{2}/[0-9]{2}/[0-9]{4} | [0-9]{4}-[0-9]{2}-[0-9]{2}

AFD — M_date = (Q, Σ, δ, q0, F)

    Q = {q0, A1, A2, AS1, A3, A4, AS2, A5, A6, A7, A8,
              B3, B4, BS1, B5, B6, BS2, B7, B8}
    Σ = {DIGIT, SLASH, DASH, ELSE}
    q0 = q0
    F = {A8, B8}

Los dos caminos divergen en el estado A2:
    A2 + SLASH  → AS1   (Formato F1: DD/MM/YYYY)
    A2 + DIGIT  → B3    (Formato F2: YYYY-MM-DD — tercer dígito del año)

Tabla de transiciones δ:

Estado │ DIGIT │ SLASH │ DASH │ ELSE
───────┼───────┼───────┼──────┼─────
  q0   │  A1   │   —   │  —   │  —
  A1   │  A2   │   —   │  —   │  —
  A2   │  B3   │  AS1  │  —   │  —     ← punto de bifurcación F1/F2
  AS1  │  A3   │   —   │  —   │  —
  A3   │  A4   │   —   │  —   │  —
  A4   │   —   │  AS2  │  —   │  —
  AS2  │  A5   │   —   │  —   │  —
  A5   │  A6   │   —   │  —   │  —
  A6   │  A7   │   —   │  —   │  —
  A7   │  A8★  │   —   │  —   │  —
  ─────────────────────────────────
  B3   │  B4   │   —   │  —   │  —
  B4   │   —   │   —   │  BS1 │  —
  BS1  │  B5   │   —   │  —   │  —
  B5   │  B6   │   —   │  —   │  —
  B6   │   —   │   —   │  BS2 │  —
  BS2  │  B7   │   —   │  —   │  —
  B7   │  B8★  │   —   │  —   │  —
"""

from __future__ import annotations

from automata.dfa import DFA
from lexical.token_types import TokenType
from .base import BaseValidator, ValidationResult

# Días máximos por mes en año no bisiesto (índice = número de mes)
_MAX_DAYS = [0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]


def _classify(char: str) -> str:
    if char.isdigit():
        return "DIGIT"
    if char == "/":
        return "SLASH"
    if char == "-":
        return "DASH"
    return "ELSE"


class DateValidator(BaseValidator):
    """
    Validador de fechas en dos formatos: DD/MM/YYYY y YYYY-MM-DD.

    El AFD verifica la secuencia exacta de dígitos y separadores.
    El análisis sintáctico valida rangos de días, meses y años bisiestos.
    """

    token_type = TokenType.DATE

    def _build_dfa(self) -> DFA:
        # FIX C3: eliminado primer dict `transitions` (era código muerto).
        # FIX C4: eliminado estado "B2" (nunca alcanzable).
        states = {
            "q0",
            # Camino F1 (DD/MM/YYYY)
            "A1", "A2", "AS1", "A3", "A4", "AS2", "A5", "A6", "A7", "A8",
            # Camino F2 (YYYY-MM-DD) — comparte A1, A2 con F1
            "B3", "B4", "BS1", "B5", "B6", "BS2", "B7", "B8",
        }
        alphabet = {"DIGIT", "SLASH", "DASH", "ELSE"}

        transitions = {
            "q0": {"DIGIT": "A1"},
            # ── Estados compartidos (primeros 2 dígitos) ──────────────
            "A1":  {"DIGIT": "A2"},
            # ── Bifurcación en A2 ─────────────────────────────────────
            # SLASH → formato F1 (el dígito previo era parte del día DD)
            # DIGIT → formato F2 (el dígito previo era parte del año YYYY)
            "A2":  {"SLASH": "AS1", "DIGIT": "B3"},
            # ── Formato F1: DD/MM/YYYY ────────────────────────────────
            "AS1": {"DIGIT": "A3"},
            "A3":  {"DIGIT": "A4"},
            "A4":  {"SLASH": "AS2"},
            "AS2": {"DIGIT": "A5"},
            "A5":  {"DIGIT": "A6"},
            "A6":  {"DIGIT": "A7"},
            "A7":  {"DIGIT": "A8"},     # ★ aceptación F1
            # ── Formato F2: YYYY-MM-DD ────────────────────────────────
            # B3 = 3er dígito del año; B4 = 4to dígito
            "B3":  {"DIGIT": "B4"},
            "B4":  {"DASH": "BS1"},     # primer '-'
            "BS1": {"DIGIT": "B5"},
            "B5":  {"DIGIT": "B6"},
            "B6":  {"DASH": "BS2"},     # segundo '-'
            "BS2": {"DIGIT": "B7"},
            "B7":  {"DIGIT": "B8"},     # ★ aceptación F2
        }

        return DFA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state="q0",
            accept_states={"A8", "B8"},
            char_classifier=_classify,
            name="AFD Fecha",
            description=(
                "Reconoce fechas en formato DD/MM/YYYY (F1) y YYYY-MM-DD (F2).\n"
                "Los dos caminos comparten los primeros 2 dígitos (A1-A2) y "
                "divergen en A2: SLASH inicia F1, DIGIT inicia F2.\n"
                "La validación sintáctica comprueba rangos reales y bisiestos."
            ),
            regex_theory=r"[0-9]{2}/[0-9]{2}/[0-9]{4}|[0-9]{4}-[0-9]{2}-[0-9]{2}",
        )

    def validate(self, value: str) -> ValidationResult:
        """
        Valida la fecha con el AFD y análisis sintáctico.

        Fases:
        1. AFD  → estructura de dígitos y separadores correcta
        2. Sintáctico → rangos válidos de día, mes y año; bisiestos
        """
        errors: list[str] = []

        accepted, trace = self._dfa.process_with_trace(value)
        trace_text = "\n".join(s.to_str() for s in trace)
        trace_text += f"\n\n{'ACEPTADA ✓' if accepted else 'RECHAZADA ✗'}"

        if not accepted:
            errors.append("Estructura inválida. Use DD/MM/YYYY o YYYY-MM-DD")
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        # ── Fase 2: Análisis sintáctico ──────────────────────────────
        if "/" in value:
            parts = value.split("/")
            day_s, month_s, year_s = parts[0], parts[1], parts[2]
            fmt = "DD/MM/YYYY"
        else:
            parts = value.split("-")
            year_s, month_s, day_s = parts[0], parts[1], parts[2]
            fmt = "YYYY-MM-DD"

        day   = _to_int(day_s)
        month = _to_int(month_s)
        year  = _to_int(year_s)

        if not 1 <= month <= 12:
            errors.append(f"Mes inválido: {month} (debe estar entre 1 y 12)")
        else:
            max_d = _max_days(year, month)
            if not 1 <= day <= max_d:
                errors.append(
                    f"Día inválido: {day} para el mes {month}/{year} (máximo {max_d})"
                )
        if year < 1:
            errors.append("El año debe ser mayor que 0")

        is_valid = len(errors) == 0
        components = {
            "formato": fmt,
            "día":     day_s,
            "mes":     month_s,
            "año":     year_s,
        }
        syntax_tree = {
            "FECHA": {
                "formato": fmt,
                "día":     day_s,
                "mes":     month_s,
                "año":     year_s,
            }
        }

        return ValidationResult(
            is_valid=is_valid,
            value=value,
            errors=errors,
            components=components,
            syntax_tree=syntax_tree,
            trace_text=trace_text,
        )


# ── Utilidades ────────────────────────────────────────────────────────────

def _to_int(s: str) -> int:
    """Convierte una cadena de dígitos a entero sin usar int() con base."""
    total = 0
    for ch in s:
        if ch.isdigit():
            total = total * 10 + (ord(ch) - ord("0"))
    return total


def _max_days(year: int, month: int) -> int:
    """Retorna el número máximo de días en un mes dado el año."""
    if month == 2:
        bisiesto = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
        return 29 if bisiesto else 28
    return _MAX_DAYS[month]
