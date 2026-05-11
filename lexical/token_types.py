"""
Definición de tipos de tokens reconocidos por el Lexer.

Un token es la unidad mínima de información reconocida por el analizador
léxico. Cada tipo de token corresponde a un patrón descrito formalmente
mediante una expresión regular y reconocido por un AFD.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """
    Tipos de tokens reconocidos por el sistema.

    Cada valor corresponde a un patrón formal implementado como AFD.
    """

    EMAIL = auto()       # Correo electrónico
    PHONE = auto()       # Número telefónico colombiano
    DATE = auto()        # Fecha (DD/MM/YYYY o YYYY-MM-DD)
    URL = auto()         # Dirección web
    PLATE = auto()       # Placa vehicular colombiana
    USERNAME = auto()    # Nombre de usuario
    PASSWORD = auto()    # Contraseña segura
    UNKNOWN = auto()     # Token no reconocido

    def label(self) -> str:
        """Etiqueta legible para la UI."""
        labels = {
            TokenType.EMAIL: "EMAIL",
            TokenType.PHONE: "TELÉFONO",
            TokenType.DATE: "FECHA",
            TokenType.URL: "URL",
            TokenType.PLATE: "PLACA",
            TokenType.USERNAME: "USUARIO",
            TokenType.PASSWORD: "CONTRASEÑA",
            TokenType.UNKNOWN: "DESCONOCIDO",
        }
        return labels[self]

    def color(self) -> str:
        """Color hexadecimal asociado al tipo de token."""
        colors = {
            TokenType.EMAIL: "#4CAF50",
            TokenType.PHONE: "#2196F3",
            TokenType.DATE: "#FF9800",
            TokenType.URL: "#9C27B0",
            TokenType.PLATE: "#F44336",
            TokenType.USERNAME: "#00BCD4",
            TokenType.PASSWORD: "#795548",
            TokenType.UNKNOWN: "#9E9E9E",
        }
        return colors[self]

    def regex_theory(self) -> str:
        """Expresión regular teórica equivalente (no se usa re de Python)."""
        regexes = {
            TokenType.EMAIL: r"[a-zA-Z0-9._\-]+@[a-zA-Z0-9\-]+\.[a-zA-Z]{2,}",
            TokenType.PHONE: r"(\+57)?3[0-9]{9}|3[0-9]{2}-[0-9]{3}-[0-9]{4}",
            TokenType.DATE: r"\d{2}/\d{2}/\d{4}|\d{4}-\d{2}-\d{2}",
            TokenType.URL: r"https?://[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}(/[^\s]*)?",
            TokenType.PLATE: r"[A-Z]{3}[0-9]{3}",
            TokenType.USERNAME: r"[a-zA-Z][a-zA-Z0-9_.\-]{2,19}",
            TokenType.PASSWORD: r"(?=.*[A-Z])(?=.*[a-z])(?=.*\d)(?=.*[@$!%*?&]).{8,}",
            TokenType.UNKNOWN: r".*",
        }
        return regexes[self]


@dataclass
class Token:
    """
    Representa un token identificado en el texto fuente.

    Attributes
    ----------
    type      : Tipo de token (TokenType)
    value     : Cadena exacta tal como aparece en el texto
    start     : Posición inicial (0-indexed) en el texto
    end       : Posición final exclusiva
    is_valid  : True si el token cumple todas las reglas sintácticas
    line      : Número de línea (1-indexed)
    column    : Columna inicial (1-indexed)
    details   : Diccionario con detalles del análisis sintáctico
    """

    type: TokenType
    value: str
    start: int
    end: int
    is_valid: bool = True
    line: int = 1
    column: int = 1
    details: dict = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.details is None:
            self.details = {}

    @property
    def length(self) -> int:
        return self.end - self.start

    @property
    def position_str(self) -> str:
        return f"L{self.line}:C{self.column} ({self.start}-{self.end})"

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Token({self.type.label()}, {self.value!r}, "
            f"pos={self.start}-{self.end}, valid={self.is_valid})"
        )
