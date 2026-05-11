"""
Validador de correos electrónicos mediante AFD.

Expresión regular teórica (no se usa re):
    [a-zA-Z0-9._-]+  @  [a-zA-Z0-9-]+  \.  [a-zA-Z]{2,6}

AFD — M_email = (Q, Σ, δ, q0, F)
    Q  = {q0, q1, q2, q3, q4, q5}
    Σ  = {ALPHA, DIGIT, DOT, UNDER, DASH, AT, ELSE}
    q0 = q0 (inicio)
    F  = {q5}

Tabla de transiciones δ:
    ┌──────┬───────┬───────┬─────┬───────┬──────┬────┬──────┐
    │Estado│ ALPHA │ DIGIT │ DOT │ UNDER │ DASH │ AT │ ELSE │
    ├──────┼───────┼───────┼─────┼───────┼──────┼────┼──────┤
    │  q0  │  q1   │  q1   │  —  │   —   │  —   │ —  │  —   │
    │  q1  │  q1   │  q1   │  q1 │   q1  │  q1  │ q2 │  —   │
    │  q2  │  q3   │  q3   │  —  │   —   │  —   │ —  │  —   │
    │  q3  │  q3   │  q3   │  q4 │   —   │  q3  │ —  │  —   │
    │  q4  │  q5   │  —   │  —  │   —   │  —   │ —  │  —   │
    │  q5  │  q5   │  —   │  —  │   —   │  —   │ —  │  —   │
    └──────┴───────┴───────┴─────┴───────┴──────┴────┴──────┘
    (— implica transición al estado trampa DEAD)

Análisis sintáctico post-AFD:
    Se descompone el email en: usuario | @ | dominio | . | extensión
    y se validan restricciones adicionales (extensión mínima 2 chars,
    el usuario no puede comenzar ni terminar con punto, etc.)
"""

from __future__ import annotations

from automata.dfa import DFA
from lexical.token_types import TokenType
from .base import BaseValidator, ValidationResult


def _classify(char: str) -> str:
    """Función de clasificación de caracteres para el AFD de email."""
    if char.isalpha():
        return "ALPHA"
    if char.isdigit():
        return "DIGIT"
    if char == ".":
        return "DOT"
    if char == "_":
        return "UNDER"
    if char == "-":
        return "DASH"
    if char == "@":
        return "AT"
    return "ELSE"


class EmailValidator(BaseValidator):
    """
    Validador de correos electrónicos.

    Implementa el AFD descrito en el módulo docstring más
    validaciones sintácticas adicionales sobre la estructura.
    """

    token_type = TokenType.EMAIL

    def _build_dfa(self) -> DFA:
        states = {"q0", "q1", "q2", "q3", "q4", "q5"}
        alphabet = {"ALPHA", "DIGIT", "DOT", "UNDER", "DASH", "AT", "ELSE"}

        transitions = {
            # q0: inicio — solo acepta ALPHA o DIGIT como primer carácter
            "q0": {
                "ALPHA": "q1",
                "DIGIT": "q1",
            },
            # q1: leyendo usuario (antes del @)
            "q1": {
                "ALPHA": "q1",
                "DIGIT": "q1",
                "DOT":   "q1",
                "UNDER": "q1",
                "DASH":  "q1",
                "AT":    "q2",
            },
            # q2: se leyó el @; espera inicio del dominio
            "q2": {
                "ALPHA": "q3",
                "DIGIT": "q3",
            },
            # q3: leyendo dominio
            "q3": {
                "ALPHA": "q3",
                "DIGIT": "q3",
                "DASH":  "q3",
                "DOT":   "q4",
            },
            # q4: se leyó el punto separador; espera inicio de extensión
            "q4": {
                "ALPHA": "q5",
            },
            # q5: leyendo extensión (estado de aceptación)
            "q5": {
                "ALPHA": "q5",
            },
        }

        return DFA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state="q0",
            accept_states={"q5"},
            char_classifier=_classify,
            name="AFD Email",
            description=(
                "Reconoce correos con formato usuario@dominio.ext. "
                "El usuario puede contener letras, dígitos, puntos, "
                "guiones y guiones bajos. El dominio solo letras, "
                "dígitos y guiones. La extensión solo letras."
            ),
            regex_theory=r"[a-zA-Z0-9._\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z]{2,6}",
        )

    def validate(self, value: str) -> ValidationResult:
        """
        Valida el email con el AFD y luego con análisis sintáctico.

        Análisis sintáctico verifica:
        1. Presencia exacta de un solo '@'
        2. Longitud mínima del usuario (≥ 1 carácter)
        3. Longitud mínima del dominio (≥ 1 carácter)
        4. Extensión de 2 a 6 caracteres
        5. El usuario no empieza ni termina con punto
        6. No hay puntos consecutivos
        """
        errors: list[str] = []

        # ── Fase 1: AFD ──────────────────────────────────────────────
        accepted, trace = self._dfa.process_with_trace(value)

        trace_lines = [s.to_str() for s in trace]
        trace_text = "\n".join(trace_lines)
        trace_text += f"\n\n{'ACEPTADA ✓' if accepted else 'RECHAZADA ✗'}"

        if not accepted:
            errors.append("Estructura general inválida (rechazada por el AFD)")
            return ValidationResult(
                is_valid=False,
                value=value,
                errors=errors,
                trace_text=trace_text,
            )

        # ── Fase 2: Análisis sintáctico ───────────────────────────────
        # Descomponer manualmente (sin re)
        at_count = value.count("@")
        if at_count != 1:
            errors.append(f"Debe contener exactamente un '@', encontrados: {at_count}")
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        at_idx = value.index("@")
        user_part = value[:at_idx]
        rest = value[at_idx + 1:]

        # Buscar el último punto en la parte de dominio
        dot_idx = _last_dot(rest)
        if dot_idx == -1:
            errors.append("Falta el punto separador entre dominio y extensión")
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        domain_part = rest[:dot_idx]
        ext_part = rest[dot_idx + 1:]

        # Validar usuario
        if len(user_part) < 1:
            errors.append("El usuario no puede estar vacío")
        if user_part.startswith(".") or user_part.endswith("."):
            errors.append("El usuario no puede comenzar ni terminar con punto")
        if ".." in user_part:
            errors.append("El usuario no puede contener puntos consecutivos")

        # Validar dominio
        if len(domain_part) < 1:
            errors.append("El dominio no puede estar vacío")
        if domain_part.startswith("-") or domain_part.endswith("-"):
            errors.append("El dominio no puede comenzar ni terminar con guión")

        # Validar extensión
        if len(ext_part) < 2:
            errors.append("La extensión debe tener al menos 2 caracteres")
        if len(ext_part) > 6:
            errors.append("La extensión no debe superar 6 caracteres")

        is_valid = len(errors) == 0

        components = {
            "usuario": user_part,
            "@": "@",
            "dominio": domain_part,
            "punto": ".",
            "extensión": ext_part,
        }

        syntax_tree = {
            "EMAIL": {
                "usuario": user_part,
                "@": "@",
                "dominio": {
                    "nombre": domain_part,
                    ".": ".",
                    "extensión": ext_part,
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


def _last_dot(s: str) -> int:
    """Retorna el índice del último punto en s, o -1 si no hay."""
    for i in range(len(s) - 1, -1, -1):
        if s[i] == ".":
            return i
    return -1
