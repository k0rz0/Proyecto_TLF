"""
Validador de placas vehiculares colombianas mediante AFD.

Formato principal (automóviles):
    AAA000  →  3 letras mayúsculas + 3 dígitos  (ej. ABC123)

Formato motos (opcional):
    AAA00A  →  3 letras + 2 dígitos + 1 letra

Expresión regular teórica:
    [A-Z]{3}[0-9]{3}  |  [A-Z]{3}[0-9]{2}[A-Z]

AFD:
    q0 -UPPER→ L1 -UPPER→ L2 -UPPER→ L3 -DIGIT→ N1 -DIGIT→ N2 -DIGIT→ N3★
                                              └─DIGIT→ N1 -DIGIT→ N2 -UPPER→ M★
"""

from __future__ import annotations

from automata.dfa import DFA
from lexical.token_types import TokenType
from .base import BaseValidator, ValidationResult


def _classify(char: str) -> str:
    if char.isupper():
        return "UPPER"
    if char.isdigit():
        return "DIGIT"
    return "ELSE"


class PlateValidator(BaseValidator):
    """
    Validador de placas colombianas.

    Reconoce formato automóvil (AAA000) y moto (AAA00A).
    """

    token_type = TokenType.PLATE

    def _build_dfa(self) -> DFA:
        states = {"q0", "L1", "L2", "L3", "N1", "N2", "N3", "M"}
        alphabet = {"UPPER", "DIGIT", "ELSE"}

        transitions = {
            "q0": {"UPPER": "L1"},
            "L1": {"UPPER": "L2"},
            "L2": {"UPPER": "L3"},
            "L3": {"DIGIT": "N1"},
            "N1": {"DIGIT": "N2"},
            "N2": {"DIGIT": "N3", "UPPER": "M"},  # N3→auto, M→moto
        }

        return DFA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state="q0",
            accept_states={"N3", "M"},
            char_classifier=_classify,
            name="AFD Placa",
            description=(
                "Reconoce placas colombianas: automóviles AAA000 y motos AAA00A. "
                "Solo se aceptan letras mayúsculas."
            ),
            regex_theory=r"[A-Z]{3}[0-9]{3}|[A-Z]{3}[0-9]{2}[A-Z]",
        )

    def validate(self, value: str) -> ValidationResult:
        errors: list[str] = []

        accepted, trace = self._dfa.process_with_trace(value)
        trace_text = "\n".join(s.to_str() for s in trace)
        trace_text += f"\n\n{'ACEPTADA ✓' if accepted else 'RECHAZADA ✗'}"

        if not accepted:
            errors.append(
                "Formato inválido. Use AAA000 (automóvil) o AAA00A (moto)"
            )
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        letters = value[:3]
        rest = value[3:]

        if rest[-1].isalpha():
            fmt = "Moto (AAA00A)"
            nums = rest[:-1]
            last = rest[-1]
        else:
            fmt = "Automóvil (AAA000)"
            nums = rest
            last = None

        components = {
            "letras": letters,
            "números": nums,
            "formato": fmt,
        }
        if last:
            components["letra_final"] = last

        syntax_tree = {
            "PLACA": {
                "formato": fmt,
                "letras": letters,
                "números": nums,
            }
        }

        return ValidationResult(
            is_valid=True,
            value=value,
            errors=[],
            components=components,
            syntax_tree=syntax_tree,
            trace_text=trace_text,
        )
