"""
Analizador Sintáctico (Parser).

El parser toma la lista de tokens producida por el Lexer y realiza
el análisis estructural de cada uno:
    1. Invoca al validador correspondiente para obtener el árbol sintáctico.
    2. Construye el SyntaxTree.
    3. Retorna los resultados con toda la información para la GUI.

En este contexto académico el "parsing" consiste en descomponer cada
token en sus constituyentes jerárquicos y verificar que las relaciones
entre ellos sean válidas según la gramática del patrón.

Gramática informal de EMAIL (en notación BNF simplificada):
    <email>     ::= <usuario> "@" <dominio>
    <dominio>   ::= <nombre> "." <extensión>
    <usuario>   ::= <alphanum> { <alphanum> | "." | "_" | "-" }
    <alphanum>  ::= [a-zA-Z0-9]
    <nombre>    ::= <alphanum> { <alphanum> | "-" }
    <extensión> ::= <alpha> { <alpha> }  (longitud 2-6)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from lexical.token_types import Token, TokenType
from syntax.syntax_tree import SyntaxTree
from validators import (
    EmailValidator,
    PhoneValidator,
    DateValidator,
    UrlValidator,
    PasswordValidator,
    PlateValidator,
    UsernameValidator,
)
from validators.base import BaseValidator, ValidationResult


@dataclass
class ParseResult:
    """Resultado del análisis sintáctico de un token."""

    token: Token
    validation: ValidationResult
    syntax_tree: Optional[SyntaxTree]
    grammar_rule: str   # Regla gramatical aplicada

    @property
    def is_valid(self) -> bool:
        return self.validation.is_valid

    def tree_str(self) -> str:
        if self.syntax_tree:
            return self.syntax_tree.display()
        return "(sin árbol)"


class SyntaxParser:
    """
    Analizador sintáctico que procesa listas de tokens.

    Para cada token, el parser:
    1. Obtiene el validador adecuado.
    2. Ejecuta el análisis completo (AFD + sintáctico).
    3. Construye el árbol sintáctico.
    4. Devuelve un ParseResult.
    """

    _GRAMMAR_RULES: Dict[TokenType, str] = {
        TokenType.EMAIL: (
            "<email> → <usuario> '@' <dominio> '.' <extensión>"
        ),
        TokenType.PHONE: (
            "<teléfono> → ['+57'] '3' <dígitos×9>"
        ),
        TokenType.DATE: (
            "<fecha> → <DD>'/'<MM>'/'<YYYY>  |  <YYYY>'-'<MM>'-'<DD>"
        ),
        TokenType.URL: (
            "<url> → ('http'|'https') '://' <dominio> '.' <ext> ['/' <ruta>]"
        ),
        TokenType.PLATE: (
            "<placa> → <LETRA×3> <DÍGITO×3>  |  <LETRA×3> <DÍGITO×2> <LETRA>"
        ),
        TokenType.USERNAME: (
            "<usuario> → <alpha> { <alpha>|<digit>|'.'|'_'|'-' }"
        ),
        TokenType.PASSWORD: (
            "<clave> → { cualquier carácter }≥8 con mayúscula, minúscula, "
            "dígito y especial"
        ),
    }

    def __init__(self) -> None:
        self._validators: Dict[TokenType, BaseValidator] = {
            TokenType.EMAIL:    EmailValidator(),
            TokenType.PHONE:    PhoneValidator(),
            TokenType.DATE:     DateValidator(),
            TokenType.URL:      UrlValidator(),
            TokenType.PLATE:    PlateValidator(),
            TokenType.USERNAME: UsernameValidator(),
            TokenType.PASSWORD: PasswordValidator(),
        }

    def parse_token(self, token: Token) -> ParseResult:
        """Analiza un solo token y retorna su ParseResult."""
        validator = self._validators.get(token.type)
        if validator is None:
            return ParseResult(
                token=token,
                validation=_unknown_result(token.value),
                syntax_tree=None,
                grammar_rule="(sin gramática definida)",
            )

        result = validator.validate(token.value)
        tree = None
        if result.syntax_tree:
            tree = SyntaxTree.from_dict(result.syntax_tree)

        grammar = self._GRAMMAR_RULES.get(token.type, "")
        return ParseResult(
            token=token,
            validation=result,
            syntax_tree=tree,
            grammar_rule=grammar,
        )

    def parse_all(self, tokens: List[Token]) -> List[ParseResult]:
        """Analiza una lista de tokens."""
        return [self.parse_token(t) for t in tokens]

    def parse_string(
        self, value: str, token_type: TokenType
    ) -> ParseResult:
        """Analiza directamente una cadena como si fuera del tipo dado."""
        fake_token = Token(
            type=token_type,
            value=value,
            start=0,
            end=len(value),
        )
        return self.parse_token(fake_token)


def _unknown_result(value: str) -> ValidationResult:
    from validators.base import ValidationResult as VR
    return VR(
        is_valid=False,
        value=value,
        errors=["Tipo de token desconocido"],
    )
