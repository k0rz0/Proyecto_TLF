"""
Analizador Léxico (Lexer / Scanner).

El lexer recorre el texto fuente carácter a carácter y extrae tokens
usando los AFDs de cada validador.  Implementa la estrategia de
*coincidencia más larga* (maximal munch): en cada posición se prueba
cada validador y se selecciona el token de mayor longitud.

Complejidad: O(n · k · m) donde
    n = longitud del texto
    k = número de validadores
    m = longitud máxima de un token

Proceso de análisis léxico:
    1. Posición i = 0
    2. Para cada validador, correr el AFD desde i hasta el último
       estado de aceptación encontrado → candidato (tipo, fin)
    3. Elegir el candidato con mayor longitud
    4. Si hay candidato → emitir Token, avanzar i al fin del token
    5. Si no → carácter no reconocido, avanzar i en 1
    6. Repetir hasta fin del texto
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from lexical.token_types import Token, TokenType
from validators.email_validator import EmailValidator
from validators.phone_validator import PhoneValidator
from validators.date_validator import DateValidator
from validators.url_validator import UrlValidator
from validators.password_validator import PasswordValidator
from validators.plate_validator import PlateValidator
from validators.username_validator import UsernameValidator
from validators.base import BaseValidator


# Orden de prioridad: los validadores más específicos primero
_VALIDATOR_ORDER: List[TokenType] = [
    TokenType.URL,       # antes que EMAIL para evitar confusión con dominios
    TokenType.EMAIL,
    TokenType.PHONE,
    TokenType.DATE,
    TokenType.PLATE,
    TokenType.PASSWORD,
    TokenType.USERNAME,
]


class LexerStats:
    """Estadísticas del análisis léxico."""

    def __init__(self) -> None:
        self.total_tokens: int = 0
        self.valid_tokens: int = 0
        self.invalid_tokens: int = 0
        self.counts: Dict[str, int] = {}
        self.unrecognized_chars: int = 0

    def record(self, token: Token) -> None:
        self.total_tokens += 1
        label = token.type.label()
        self.counts[label] = self.counts.get(label, 0) + 1
        if token.is_valid:
            self.valid_tokens += 1
        else:
            self.invalid_tokens += 1

    def summary(self) -> str:
        lines = [
            f"Total tokens: {self.total_tokens}",
            f"  Válidos:    {self.valid_tokens}",
            f"  Inválidos:  {self.invalid_tokens}",
            f"  Caracteres no reconocidos: {self.unrecognized_chars}",
        ]
        if self.counts:
            lines.append("Por tipo:")
            for k, v in sorted(self.counts.items()):
                lines.append(f"  {k}: {v}")
        return "\n".join(lines)


class Lexer:
    """
    Analizador léxico basado en AFDs.

    Uso
    ---
    lexer = Lexer()
    tokens = lexer.tokenize(text)
    stats  = lexer.stats
    """

    def __init__(self) -> None:
        self._validators: Dict[TokenType, BaseValidator] = {
            TokenType.URL:      UrlValidator(),
            TokenType.EMAIL:    EmailValidator(),
            TokenType.PHONE:    PhoneValidator(),
            TokenType.DATE:     DateValidator(),
            TokenType.PLATE:    PlateValidator(),
            TokenType.PASSWORD: PasswordValidator(),
            TokenType.USERNAME: UsernameValidator(),
        }
        self.stats: LexerStats = LexerStats()

    # ------------------------------------------------------------------
    # Interfaz pública
    # ------------------------------------------------------------------

    def tokenize(self, text: str) -> List[Token]:
        """
        Analiza `text` y retorna la lista de tokens encontrados.

        Solo se devuelven tokens reconocidos por algún validador.
        Los caracteres entre tokens (espacios, puntuación, etc.) se ignoran
        como separadores naturales del lenguaje fuente.
        """
        self.stats = LexerStats()
        tokens: List[Token] = []
        i = 0
        n = len(text)

        while i < n:
            # Saltar separadores obvios (espacios, tabulaciones, saltos)
            if text[i] in (" ", "\t", "\n", "\r", ",", ";"):
                i += 1
                continue

            best = self._best_match(text, i)

            if best is None:
                self.stats.unrecognized_chars += 1
                i += 1
                continue

            token_type, end_pos = best
            raw_value = text[i:end_pos]

            # Validación completa (AFD + sintáctico) para determinar is_valid
            validator = self._validators[token_type]
            result = validator.validate(raw_value)

            # Calcular línea y columna
            line, col = _line_col(text, i)

            token = Token(
                type=token_type,
                value=raw_value,
                start=i,
                end=end_pos,
                is_valid=result.is_valid,
                line=line,
                column=col,
                details={
                    "errors": result.errors,
                    "components": result.components,
                    "syntax_tree": result.syntax_tree,
                },
            )
            tokens.append(token)
            self.stats.record(token)
            i = end_pos

        return tokens

    def tokenize_word_boundary(self, text: str) -> List[Token]:
        """
        Variante de tokenize que también prueba palabras delimitadas
        por espacios/puntuación, útil para analizar párrafos.
        """
        tokens: List[Token] = []
        words = _split_words(text)
        for word, start in words:
            best = self._best_match(word, 0)
            if best is None:
                continue
            token_type, end_rel = best
            if end_rel < len(word):
                continue   # coincidencia parcial → ignorar
            raw = word
            validator = self._validators[token_type]
            result = validator.validate(raw)
            line, col = _line_col(text, start)
            token = Token(
                type=token_type,
                value=raw,
                start=start,
                end=start + len(raw),
                is_valid=result.is_valid,
                line=line,
                column=col,
                details={
                    "errors": result.errors,
                    "components": result.components,
                    "syntax_tree": result.syntax_tree,
                },
            )
            tokens.append(token)
            self.stats.record(token)
        return tokens

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

    def _best_match(
        self, text: str, start: int
    ) -> Optional[Tuple[TokenType, int]]:
        """
        Encuentra la coincidencia más larga en `text` a partir de `start`.

        Retorna (TokenType, end_pos) o None si ningún validador coincide.
        """
        best_type: Optional[TokenType] = None
        best_end: int = start

        for token_type in _VALIDATOR_ORDER:
            validator = self._validators[token_type]
            end = validator.find_longest_match(text, start)
            if end > best_end:
                best_end = end
                best_type = token_type
            elif end == best_end and best_type is not None:
                # Empate: respetar prioridad del orden
                pass

        if best_type is None:
            return None
        return best_type, best_end

    def get_validator(self, token_type: TokenType) -> BaseValidator:
        return self._validators[token_type]


# ---------------------------------------------------------------------------
# Utilidades de posición
# ---------------------------------------------------------------------------

def _line_col(text: str, pos: int) -> Tuple[int, int]:
    """Calcula (línea, columna) 1-indexed para la posición `pos`."""
    line = 1
    col = 1
    for i, ch in enumerate(text):
        if i == pos:
            break
        if ch == "\n":
            line += 1
            col = 1
        else:
            col += 1
    return line, col


def _split_words(text: str) -> List[Tuple[str, int]]:
    """Divide el texto en palabras con sus posiciones de inicio."""
    words: List[Tuple[str, int]] = []
    separators = set(" \t\n\r,;()[]{}\"'")
    i = 0
    n = len(text)
    while i < n:
        if text[i] in separators:
            i += 1
            continue
        j = i
        while j < n and text[j] not in separators:
            j += 1
        words.append((text[i:j], i))
        i = j
    return words
