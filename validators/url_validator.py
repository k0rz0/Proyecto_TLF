"""
Validador de URLs mediante AFD.

Formatos aceptados:
    http://dominio.ext[/ruta]
    https://dominio.ext[/ruta]

Expresión regular teórica:
    https?://[a-zA-Z0-9.\-]+(:[0-9]+)?(/[^\s]*)?

AFD — M_url = (Q, Σ, δ, q0, F):

    Q  = {q0, H1, H2, H3, H4, HS, C1, C2, D0, D1, DOT, E1, PATH}
    Σ  = {H, T, P, S, COLON, SLASH, DOT, DASH, UNDER, ALPHA, DIGIT,
           QUERY, HASH, EQ, AMP, PCT, ELSE}
    q0 = q0
    F  = {E1, PATH}

    Camino del protocolo:
        q0 -H→ H1 -T→ H2 -T→ H3 -P→ H4
        H4 -S→ HS  (HTTPS)   H4 -COLON→ C1  (HTTP directo)
        HS -COLON→ C1

    Separador "://":
        C1 -SLASH→ C2 -SLASH→ D0

    Dominio:
        D0 -[letra|dígito]→ D1 -[letra|dígito|dash|under]→ D1
        D1 -DOT→ DOT

    Extensión (F):
        DOT -ALPHA→ E1 -ALPHA→ E1  ★
        E1  -DOT→ DOT              (subdominio adicional)
        E1  -SLASH→ PATH           (inicio de ruta)
        PATH -[cualquier]→ PATH    ★

CORRECCIÓN C1: D0 ahora incluye T, P, S además de H y ALPHA/DIGIT,
ya que el clasificador los separa de ALPHA para reconocer el protocolo.
"""

from __future__ import annotations

from automata.dfa import DFA
from lexical.token_types import TokenType
from .base import BaseValidator, ValidationResult

# Letras del protocolo que el clasificador separa de ALPHA
_PROTO_LETTERS = {"H", "T", "P", "S"}
# Clases de símbolo que representan "cualquier letra o dígito" en el dominio
_DOM_ALPHANUM = {"ALPHA", "DIGIT"} | _PROTO_LETTERS


def _classify(char: str) -> str:
    """
    Clasifica un carácter en su clase de símbolo para el AFD de URL.

    Las letras h, t, p, s se clasifican individualmente para que el AFD
    pueda reconocer el protocolo 'http'/'https'. Dentro del dominio y la
    ruta se tratan igual que ALPHA.
    """
    if char == "h":
        return "H"
    if char == "t":
        return "T"
    if char == "p":
        return "P"
    if char == "s":
        return "S"
    if char == ":":
        return "COLON"
    if char == "/":
        return "SLASH"
    if char == ".":
        return "DOT"
    if char == "-":
        return "DASH"
    if char == "_":
        return "UNDER"
    if char == "?":
        return "QUERY"
    if char == "#":
        return "HASH"
    if char == "=":
        return "EQ"
    if char == "&":
        return "AMP"
    if char == "%":
        return "PCT"
    if char.isalpha():
        return "ALPHA"
    if char.isdigit():
        return "DIGIT"
    return "ELSE"


def _dom_trans(to_state: str) -> dict:
    """Genera transiciones desde cualquier clase letra/dígito hacia to_state."""
    return {cls: to_state for cls in _DOM_ALPHANUM}


class UrlValidator(BaseValidator):
    """
    Validador de URLs http/https.

    El AFD verifica la estructura protocolo + :// + dominio + extensión.
    El análisis sintáctico verifica:
      - Protocolo correcto (http o https)
      - Dominio no vacío
      - Extensión de mínimo 2 caracteres
    """

    token_type = TokenType.URL

    def _build_dfa(self) -> DFA:
        states = {
            "q0",
            # protocolo
            "H1", "H2", "H3", "H4", "HS",
            # separador ://
            "C1", "C2",
            # dominio
            "D0", "D1",
            # punto separador y extensión
            "DOT", "E1",
            # ruta opcional
            "PATH",
        }
        alphabet = {
            "H", "T", "P", "S", "COLON", "SLASH", "DOT",
            "DASH", "UNDER", "ALPHA", "DIGIT", "QUERY",
            "HASH", "EQ", "AMP", "PCT", "ELSE",
        }

        transitions = {
            # ── Protocolo ─────────────────────────────────────────────
            "q0": {"H": "H1"},
            "H1": {"T": "H2"},
            "H2": {"T": "H3"},
            "H3": {"P": "H4"},
            "H4": {"S": "HS", "COLON": "C1"},
            "HS": {"COLON": "C1"},
            # ── :// ───────────────────────────────────────────────────
            "C1": {"SLASH": "C2"},
            "C2": {"SLASH": "D0"},
            # ── Dominio (FIX C1: incluir T, P, S como inicio válido) ──
            "D0": {**_dom_trans("D1")},
            "D1": {
                **_dom_trans("D1"),
                "DASH":  "D1",
                "UNDER": "D1",
                "DOT":   "DOT",
            },
            # ── Punto separador ───────────────────────────────────────
            "DOT": {cls: "E1" for cls in _DOM_ALPHANUM},
            # ── Extensión ★ ───────────────────────────────────────────
            "E1": {
                **_dom_trans("E1"),
                "DIGIT": "E1",
                "DOT":   "DOT",   # subdominio adicional
                "SLASH": "PATH",  # inicio de ruta
            },
            # ── Ruta ★ ───────────────────────────────────────────────
            "PATH": {
                **_dom_trans("PATH"),
                "SLASH": "PATH", "DOT":   "PATH", "DASH":  "PATH",
                "UNDER": "PATH", "QUERY": "PATH", "HASH":  "PATH",
                "EQ":    "PATH", "AMP":   "PATH", "PCT":   "PATH",
            },
        }

        return DFA(
            states=states,
            alphabet=alphabet,
            transitions=transitions,
            initial_state="q0",
            accept_states={"E1", "PATH"},
            char_classifier=_classify,
            name="AFD URL",
            description=(
                "Reconoce URLs con protocolo http o https, dominio y extensión. "
                "La ruta es opcional. Admite subdominios y parámetros de consulta.\n"
                "Las letras h, t, p, s se clasifican individualmente para reconocer "
                "el protocolo; en dominio y ruta se tratan como letras normales."
            ),
            regex_theory=r"https?://[a-zA-Z0-9.\-]+(:[0-9]+)?(/[^\s]*)?",
        )

    def validate(self, value: str) -> ValidationResult:
        """
        Valida la URL con el AFD y análisis sintáctico.

        Fases:
        1. AFD → estructura general
        2. Sintáctico → protocolo, dominio, extensión
        """
        errors: list[str] = []

        accepted, trace = self._dfa.process_with_trace(value)
        trace_text = "\n".join(s.to_str() for s in trace)
        trace_text += f"\n\n{'ACEPTADA ✓' if accepted else 'RECHAZADA ✗'}"

        if not accepted:
            errors.append("URL inválida. Formato esperado: http(s)://dominio.ext")
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        # ── Fase 2: Análisis sintáctico ──────────────────────────────
        # Extraer protocolo
        if value.startswith("https://"):
            protocol = "https"
            rest = value[8:]
        elif value.startswith("http://"):
            protocol = "http"
            rest = value[7:]
        else:
            errors.append("Protocolo desconocido (se esperaba http o https)")
            return ValidationResult(
                is_valid=False, value=value, errors=errors, trace_text=trace_text
            )

        # Separar host (dominio+ext) de la ruta
        slash_idx = _find_char(rest, "/")
        if slash_idx >= 0:
            domain_full = rest[:slash_idx]
            path = rest[slash_idx:]
        else:
            domain_full = rest
            path = ""

        # Separar extensión (FIX C2: bloque único, sin duplicación)
        dot_idx = _last_dot_idx(domain_full)
        if dot_idx < 0:
            errors.append("Falta la extensión del dominio (ej. .com, .edu)")
            domain, extension = domain_full, ""
        else:
            domain = domain_full[:dot_idx]
            extension = domain_full[dot_idx + 1:]
            if len(domain) < 1:
                errors.append("El dominio no puede estar vacío")
            if len(extension) < 2:
                errors.append("La extensión debe tener al menos 2 caracteres")

        is_valid = len(errors) == 0
        components = {
            "protocolo": protocol,
            "dominio": domain if dot_idx >= 0 else domain_full,
            "extensión": extension,
            "ruta": path or "(ninguna)",
        }
        syntax_tree = {
            "URL": {
                "protocolo": protocol,
                "host": {
                    "dominio": domain if dot_idx >= 0 else domain_full,
                    ".": ".",
                    "extensión": extension,
                },
                "ruta": path or "/",
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

def _find_char(s: str, c: str) -> int:
    """Retorna el índice de la primera ocurrencia de c en s, o -1."""
    for i, ch in enumerate(s):
        if ch == c:
            return i
    return -1


def _last_dot_idx(s: str) -> int:
    """Retorna el índice del último '.' en s, o -1."""
    for i in range(len(s) - 1, -1, -1):
        if s[i] == ".":
            return i
    return -1
