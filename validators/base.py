"""
Interfaz base para todos los validadores del sistema.

Cada validador encapsula un AFD y añade lógica de análisis sintáctico
sobre el resultado del autómata: descompone la cadena en sus partes
estructurales y genera un árbol sintáctico simplificado.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from automata.dfa import DFA


@dataclass
class ValidationResult:
    """
    Resultado completo de la validación de una cadena.

    Attributes
    ----------
    is_valid      : True si la cadena es aceptada por el AFD y cumple
                    las reglas sintácticas adicionales.
    value         : Cadena analizada.
    errors        : Lista de mensajes de error (vacía si es válido).
    components    : Partes estructurales identificadas (ej. usuario, dominio).
    syntax_tree   : Árbol sintáctico simplificado como dict anidado.
    trace_text    : Traza de estados del AFD (para el simulador).
    """

    is_valid: bool
    value: str
    errors: List[str] = field(default_factory=list)
    components: Dict[str, str] = field(default_factory=dict)
    syntax_tree: Dict = field(default_factory=dict)
    trace_text: str = ""

    def summary(self) -> str:
        if self.is_valid:
            return f"✓ VÁLIDO: {self.value}"
        return f"✗ INVÁLIDO: {self.value}  →  {'; '.join(self.errors)}"


class BaseValidator(ABC):
    """
    Clase base abstracta para validadores basados en AFD.

    Subclases deben implementar:
        _build_dfa()       → construir y retornar el DFA
        _parse(value)      → análisis sintáctico, retorna ValidationResult
        token_type         → propiedad que retorna el TokenType
    """

    def __init__(self) -> None:
        self._dfa: DFA = self._build_dfa()

    @property
    def dfa(self) -> DFA:
        return self._dfa

    @abstractmethod
    def _build_dfa(self) -> DFA:
        """Construye y retorna el AFD del validador."""

    @abstractmethod
    def validate(self, value: str) -> ValidationResult:
        """
        Valida `value` usando el AFD y análisis sintáctico.
        Retorna un ValidationResult con todos los detalles.
        """

    def quick_check(self, value: str) -> bool:
        """Validación rápida: solo el AFD, sin análisis sintáctico."""
        return self._dfa.process(value)

    def find_longest_match(self, text: str, start: int) -> int:
        """
        Encuentra el final de la coincidencia más larga que empieza en `start`.
        Delega en el método homónimo del DFA.
        """
        return self._dfa.find_longest_match(text, start)
