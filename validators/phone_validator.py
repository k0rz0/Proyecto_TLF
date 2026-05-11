"""
Validador de números telefónicos colombianos mediante AFD.

Formatos aceptados:
    F1: 10 dígitos comenzando con 3          →  3001234567
    F2: Indicativo +57 + 10 dígitos          →  +573001234567
    F3: Grupos separados por guión            →  300-123-4567

Expresión regular teórica:
    (\+57)?3[0-9]{9} | 3[0-9]{2}-[0-9]{3}-[0-9]{4}

AFD — M_phone = (Q, Σ, δ, q0, F)

    Q  = {q0, PLUS, CC5, CC7, D1…D10, G1…G9}
    Σ  = {PLUS, DASH, D3, D5, D7, DIGIT, ELSE}
    q0 = q0
    F  = {D10, G9}

    CORRECCIÓN C6: Las clases D5 ('5') y D7 ('7') son independientes de DIGIT
    para que los estados CC5 y CC7 del prefijo +57 solo acepten EXACTAMENTE
    los dígitos '5' y '7' respectivamente. Las demás posiciones del número
    aceptan todas las clases de dígito {D3, D5, D7, DIGIT}.

Tabla de transiciones δ (parcial):

Estado │ D3  │ D5  │ D7  │DIGIT│PLUS │DASH │ELSE
───────┼─────┼─────┼─────┼─────┼─────┼─────┼─────
  q0   │  D1 │  —  │  —  │  —  │PLUS │  —  │  —
  PLUS │  —  │ CC5 │  —  │  —  │  —  │  —  │  —   ← solo acepta '5'
  CC5  │  —  │  —  │ CC7 │  —  │  —  │  —  │  —   ← solo acepta '7'
  CC7  │  D1 │  —  │  —  │  —  │  —  │  —  │  —
  D1   │  D2 │  D2 │  D2 │  D2 │  —  │  —  │  —
  D2   │ D3s │ D3s │ D3s │ D3s │  —  │  —  │  —
  D3s  │  D4 │  D4 │  D4 │  D4 │  —  │  G1 │  —
  ...  │ ... │ ... │ ... │ ... │  —  │  —  │  —
  D9   │ D10★│ D10★│ D10★│ D10★│  —  │  —  │  —
  G1   │  G2 │  G2 │  G2 │  G2 │  —  │  —  │  —
  ...
  G4   │  —  │  —  │  —  │  —  │  —  │  G5 │  —
  G8   │  G9★│  G9★│  G9★│  G9★│  —  │  —  │  —
"""

from __future__ import annotations

from automata.dfa import DFA
from lexical.token_types import TokenType
from .base import BaseValidator, ValidationResult

# Clases que representan cualquier dígito válido en el número de teléfono
_ANY_DIGIT = ("D3", "D5", "D7", "DIGIT")


def _phone_seq(to: str) -> dict:
    """Genera transiciones desde cualquier dígito de teléfono hacia `to`."""
    return {cls: to for cls in _ANY_DIGIT}


def _classify(char: str) -> str:
    """
    Clasifica un carácter para el AFD de teléfono.

    D3, D5, D7 se separan de DIGIT para que el camino del prefijo +57
    pueda exigir exactamente '5' y '7' en CC5 y CC7 respectivamente.
    """
    if char == "+":
        return "PLUS"
    if char == "-":
        return "DASH"
    if char == "3":
        return "D3"
    if char == "5":
        return "D5"
    if char == "7":
        return "D7"
    if char.isdigit():
        return "DIGIT"   # 0,1,2,4,6,8,9
    return "ELSE"


class PhoneValidator(BaseValidator):
    """
    Validador de teléfonos celulares colombianos.

    El AFD reconoce tres formatos en un único autómata combinando caminos.
    La especificidad de D5/D7 garantiza que +57 no sea reemplazable por
    otro indicativo de país.
    """

    token_type = TokenType.PHONE

    def _build_dfa(self) -> DFA:
        states = {
            "q0",
            "PLUS", "CC5", "CC7",
            "D1", "D2", "D3s", "D4", "D5", "D6", "D7", "D8", "D9", "D10",
            "G1", "G2", "G3", "G4", "G5", "G6", "G7", "G8", "G9",
        }
        alphabet = {"PLUS", "DASH", "D3", "D5", "D7", "DIGIT", "ELSE"}

        transitions = {
            # ── Estado inicial ────────────────────────────────────────
            "q0":  {"PLUS": "PLUS", "D3": "D1"},

            # ── Prefijo +57 (FIX C6: D5 y D7 específicos) ────────────
            "PLUS": {"D5": "CC5"},          # acepta solo el '5' de +57
            "CC5":  {"D7": "CC7"},           # acepta solo el '7' de +57
            "CC7":  {"D3": "D1"},            # el número celular empieza con '3'

            # ── Secuencia de 10 dígitos (F1 y F2) ────────────────────
            "D1":  {**_phone_seq("D2")},
            "D2":  {**_phone_seq("D3s")},
            # D3s: 3er dígito — puede iniciar formato guiones (F3)
            "D3s": {**_phone_seq("D4"), "DASH": "G1"},
            "D4":  {**_phone_seq("D5")},
            "D5":  {**_phone_seq("D6")},
            "D6":  {**_phone_seq("D7")},
            "D7":  {**_phone_seq("D8")},
            "D8":  {**_phone_seq("D9")},
            "D9":  {**_phone_seq("D10")},
            # D10: estado de aceptación F1 y F2

            # ── Formato F3: 300-123-4567 ──────────────────────────────
            # G1-G4: grupo intermedio (3 dígitos)
            "G1": {**_phone_seq("G2")},
            "G2": {**_phone_seq("G3")},
            "G3": {**_phone_seq("G4")},
            "G4": {"DASH": "G5"},            # segundo guión (después de 3 dígitos)
            # G5-G9: grupo final (4 dígitos) → G9 aceptación
            "G5": {**_phone_seq("G6")},
            "G6": {**_phone_seq("G7")},
            "G7": {**_phone_seq("G8")},
            "G8": {**_phone_seq("G9")},
        }

        return DFA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state="q0",
            accept_states={"D10", "G9"},
            char_classifier=_classify,
            name="AFD Teléfono",
            description=(
                "Reconoce teléfonos celulares colombianos en tres formatos.\n"
                "F1: 3XXXXXXXXX (10 dígitos)\n"
                "F2: +573XXXXXXXXX (con indicativo)\n"
                "F3: 3XX-XXX-XXXX (con guiones)\n"
                "Los estados CC5 y CC7 exigen EXACTAMENTE '5' y '7'."
            ),
            regex_theory=r"(\+57)?3[0-9]{9}|3[0-9]{2}-[0-9]{3}-[0-9]{4}",
        )

    def validate(self, value: str) -> ValidationResult:
        """
        Valida el teléfono con el AFD y análisis sintáctico.

        Fases:
        1. AFD  → estructura correcta (longitud, dígitos, separadores)
        2. Sintáctico → 10 dígitos netos, comienza con 3
        """
        errors: list[str] = []

        accepted, trace = self._dfa.process_with_trace(value)
        trace_text = "\n".join(s.to_str() for s in trace)
        trace_text += f"\n\n{'ACEPTADA ✓' if accepted else 'RECHAZADA ✗'}"

        if not accepted:
            errors.append(
                "Formato inválido. Use: 3001234567, +573001234567 o 300-123-4567"
            )
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        # ── Análisis sintáctico ───────────────────────────────────────
        # Extraer dígitos netos (sin indicativo ni guiones)
        clean = value
        if clean.startswith("+57"):
            clean = clean[3:]
        clean = clean.replace("-", "")

        # Verificar longitud y primer dígito
        if len(clean) != 10:
            errors.append(f"El número debe tener 10 dígitos, tiene {len(clean)}")
        if not clean.startswith("3"):
            errors.append("El número celular colombiano debe comenzar con 3")

        # Determinar formato y componentes
        if value.startswith("+57"):
            components = {"indicativo": "+57", "número": value[3:]}
            syntax_tree = {
                "TELÉFONO": {
                    "formato": "F2 — Internacional",
                    "indicativo_país": "+57",
                    "número_local": value[3:],
                }
            }
        elif "-" in value:
            parts = value.split("-")
            components = {
                "área":   parts[0],
                "grupo1": parts[1] if len(parts) > 1 else "",
                "grupo2": parts[2] if len(parts) > 2 else "",
            }
            syntax_tree = {
                "TELÉFONO": {
                    "formato": "F3 — Con guiones",
                    "área":    parts[0],
                    "grupo_1": parts[1] if len(parts) > 1 else "",
                    "grupo_2": parts[2] if len(parts) > 2 else "",
                }
            }
        else:
            components = {"número": value}
            syntax_tree = {
                "TELÉFONO": {
                    "formato": "F1 — Local (10 dígitos)",
                    "número":  value,
                }
            }

        is_valid = len(errors) == 0
        return ValidationResult(
            is_valid=is_valid,
            value=value,
            errors=errors,
            components=components,
            syntax_tree=syntax_tree,
            trace_text=trace_text,
        )
