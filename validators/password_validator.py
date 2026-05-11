"""
Validador de contraseñas seguras.

Reglas:
    - Longitud mínima de 8 caracteres
    - Al menos una letra mayúscula  [A-Z]
    - Al menos una letra minúscula  [a-z]
    - Al menos un dígito            [0-9]
    - Al menos un carácter especial [@$!%*?&#^()_\\-+=]

Expresión regular teórica (lookaheads — conceptual, no se implementa con re):
    (?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[@$!%*?&#^()_\\-+=]).{8,}

IMPLEMENTACIÓN MEDIANTE AFD DE CONJUNTO POTENCIA (Power-set Construction):

    Como un AFD puro no puede verificar co-ocurrencia de categorías sin
    explotar el espacio de estados, aplicamos la construcción de conjunto
    potencia sobre las 4 categorías requeridas:

        bit 0 (valor 1) → ha visto mayúscula
        bit 1 (valor 2) → ha visto minúscula
        bit 2 (valor 4) → ha visto dígito
        bit 3 (valor 8) → ha visto carácter especial

    Esto genera 2^4 = 16 estados (S0000 .. S1111).

    M_password = (Q, Σ, δ, q0, F)
        Q  = {S0000, S0001, ..., S1111}   |Q| = 16
        Σ  = {UPPER, LOWER, DIGIT, SPECIAL, OTHER}
        q0 = S0000
        F  = {S1111}

    Función de transición:
        δ(Sxxxx, UPPER)   = S(xxxx | 0001)
        δ(Sxxxx, LOWER)   = S(xxxx | 0010)
        δ(Sxxxx, DIGIT)   = S(xxxx | 0100)
        δ(Sxxxx, SPECIAL) = S(xxxx | 1000)
        δ(Sxxxx, OTHER)   = S(xxxx)          ← no cambia la máscara

    Nota: la longitud mínima se verifica en el análisis sintáctico porque
    los AFDs no cuentan pasos de manera directa sin estados adicionales.
"""

from __future__ import annotations

from automata.dfa import DFA
from lexical.token_types import TokenType
from .base import BaseValidator, ValidationResult

# Conjuntos de bits
_BIT_UPPER   = 1    # 0001
_BIT_LOWER   = 2    # 0010
_BIT_DIGIT   = 4    # 0100
_BIT_SPECIAL = 8    # 1000
_ALL_BITS    = 15   # 1111 — todos los requisitos satisfechos

_SPECIAL_CHARS = frozenset("@$!%*?&#^()_-+=|~<>.,;:'\"[]{}\\`/")


def _state_name(mask: int) -> str:
    """Nombre del estado con máscara binaria de 4 bits."""
    return f"S{mask:04b}"


def _classify(char: str) -> str:
    if char.isupper():
        return "UPPER"
    if char.islower():
        return "LOWER"
    if char.isdigit():
        return "DIGIT"
    if char in _SPECIAL_CHARS:
        return "SPECIAL"
    return "OTHER"


class PasswordValidator(BaseValidator):
    """
    Validador de contraseñas mediante AFD de conjunto potencia (16 estados).

    Cada estado codifica en su nombre binario qué categorías se han visto.
    El estado S1111 es el único de aceptación.
    """

    token_type = TokenType.PASSWORD

    def _build_dfa(self) -> DFA:
        states  = {_state_name(m) for m in range(16)}
        alphabet = {"UPPER", "LOWER", "DIGIT", "SPECIAL", "OTHER"}

        bit_map = {
            "UPPER":   _BIT_UPPER,
            "LOWER":   _BIT_LOWER,
            "DIGIT":   _BIT_DIGIT,
            "SPECIAL": _BIT_SPECIAL,
            "OTHER":   0,
        }

        # Construir la tabla de transiciones programáticamente
        transitions: dict[str, dict[str, str]] = {}
        for mask in range(16):
            state = _state_name(mask)
            transitions[state] = {
                cat: _state_name(mask | bit)
                for cat, bit in bit_map.items()
            }

        # FIX: eliminada la asignación redundante de accept_states
        accept_states = {_state_name(_ALL_BITS)}   # solo S1111

        return DFA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state=_state_name(0),
            accept_states=accept_states,
            char_classifier=_classify,
            name="AFD Contraseña",
            description=(
                "AFD de conjunto potencia con 16 estados.\n"
                "Cada estado Sxxxx codifica (en binario) qué categorías "
                "se han visto: bit0=mayúscula, bit1=minúscula, "
                "bit2=dígito, bit3=especial.\n"
                "Acepta cuando todos los bits están activados (S1111).\n"
                "La longitud mínima se valida en el análisis sintáctico."
            ),
            regex_theory=r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[@$!%*?&]).{8,}",
        )

    def validate(self, value: str) -> ValidationResult:
        """
        Valida la contraseña con el AFD y análisis sintáctico.

        Fases:
        1. AFD  → verificar co-ocurrencia de categorías (16 estados)
        2. Sintáctico → longitud mínima 8, cálculo de fortaleza
        """
        errors: list[str] = []

        # Longitud mínima (el AFD no cuenta pasos directamente)
        if len(value) < 8:
            errors.append(f"Longitud mínima 8 caracteres (tiene {len(value)})")

        accepted, trace = self._dfa.process_with_trace(value)
        trace_text = "\n".join(s.to_str() for s in trace)
        trace_text += f"\n\n{'ACEPTADA ✓' if accepted else 'RECHAZADA ✗'}"

        # Diagnóstico detallado de categorías faltantes
        has_upper   = any(c.isupper()          for c in value)
        has_lower   = any(c.islower()          for c in value)
        has_digit   = any(c.isdigit()          for c in value)
        has_special = any(c in _SPECIAL_CHARS  for c in value)

        if not accepted:
            if not has_upper:
                errors.append("Falta al menos una letra mayúscula [A-Z]")
            if not has_lower:
                errors.append("Falta al menos una letra minúscula [a-z]")
            if not has_digit:
                errors.append("Falta al menos un dígito [0-9]")
            if not has_special:
                errors.append("Falta al menos un carácter especial (@$!%*?&...)")

        # Calcular fortaleza (0-5)
        checks = [has_upper, has_lower, has_digit, has_special, len(value) >= 12]
        score = sum(checks)
        strength_labels = ["Muy débil", "Débil", "Media", "Fuerte", "Muy fuerte"]
        strength = strength_labels[min(score, 4)]

        is_valid = len(errors) == 0
        components = {
            "tiene_mayúscula": "✓" if has_upper   else "✗",
            "tiene_minúscula": "✓" if has_lower   else "✗",
            "tiene_dígito":    "✓" if has_digit   else "✗",
            "tiene_especial":  "✓" if has_special else "✗",
            "longitud":        str(len(value)),
            "fortaleza":       strength,
        }
        syntax_tree = {
            "CONTRASEÑA": {
                "longitud":   len(value),
                "fortaleza":  strength,
                "requisitos": {
                    "mayúscula": has_upper,
                    "minúscula": has_lower,
                    "dígito":    has_digit,
                    "especial":  has_special,
                },
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
