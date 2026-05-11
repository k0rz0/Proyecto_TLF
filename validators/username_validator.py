"""
Validador de nombres de usuario mediante AFD.

Reglas:
    - Comienza con letra (a-z, A-Z)
    - Puede contener letras, dígitos, punto, guión y guión bajo
    - Longitud entre 3 y 20 caracteres
    - No puede terminar con punto, guión o guión bajo

Expresión regular teórica:
    [a-zA-Z][a-zA-Z0-9._\-]{2,19}

AFD:
    q0 -ALPHA→ q1 -[ALPHA|DIGIT|DOT|DASH|UNDER]→ q1
                    (validaciones de longitud y terminación en sintáctico)
"""

from __future__ import annotations

from automata.dfa import DFA
from lexical.token_types import TokenType
from .base import BaseValidator, ValidationResult


def _classify(char: str) -> str:
    if char.isalpha():
        return "ALPHA"
    if char.isdigit():
        return "DIGIT"
    if char in (".", "_", "-"):
        return "SPECIAL"
    return "ELSE"


class UsernameValidator(BaseValidator):
    """
    Validador de nombres de usuario.

    El AFD verifica que el usuario comience con letra y contenga solo
    caracteres permitidos. El análisis sintáctico verifica longitud y
    que no termine con carácter especial.
    """

    token_type = TokenType.USERNAME

    def _build_dfa(self) -> DFA:
        states = {"q0", "q1"}
        alphabet = {"ALPHA", "DIGIT", "SPECIAL", "ELSE"}

        transitions = {
            "q0": {"ALPHA": "q1"},                         # debe comenzar con letra
            "q1": {"ALPHA": "q1", "DIGIT": "q1", "SPECIAL": "q1"},
        }

        return DFA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state="q0",
            accept_states={"q1"},
            char_classifier=_classify,
            name="AFD Usuario",
            description=(
                "Reconoce nombres de usuario que comienzan con letra y "
                "contienen letras, dígitos o los símbolos . _ -"
            ),
            regex_theory=r"[a-zA-Z][a-zA-Z0-9._\-]{2,19}",
        )

    def validate(self, value: str) -> ValidationResult:
        errors: list[str] = []

        accepted, trace = self._dfa.process_with_trace(value)
        trace_text = "\n".join(s.to_str() for s in trace)
        trace_text += f"\n\n{'ACEPTADA ✓' if accepted else 'RECHAZADA ✗'}"

        if not accepted:
            errors.append(
                "El usuario debe comenzar con letra y usar solo letras, "
                "dígitos, '.', '_' o '-'"
            )
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        # Análisis sintáctico
        if len(value) < 3:
            errors.append(f"Longitud mínima 3 caracteres (tiene {len(value)})")
        if len(value) > 20:
            errors.append(f"Longitud máxima 20 caracteres (tiene {len(value)})")
        if value and value[-1] in (".", "_", "-"):
            errors.append("El usuario no puede terminar con '.', '_' o '-'")
        if ".." in value or "__" in value or "--" in value:
            errors.append("No se permiten caracteres especiales consecutivos")

        is_valid = len(errors) == 0
        components = {
            "usuario": value,
            "longitud": str(len(value)),
            "primer_carácter": value[0] if value else "",
        }
        syntax_tree = {
            "USUARIO": {
                "valor": value,
                "longitud": len(value),
                "primer_char": value[0] if value else "",
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
