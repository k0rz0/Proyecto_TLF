"""
Árbol sintáctico simplificado para representar la estructura
jerárquica de los tokens reconocidos.

El árbol es una representación en árbol n-ario donde:
    - La raíz es el tipo del token (EMAIL, URL, etc.)
    - Los nodos hijos representan los componentes estructurales
    - Las hojas son los valores terminales (cadenas)

Ejemplo para EMAIL = "user.name@company.com"

    EMAIL
    ├── usuario: "user.name"
    ├── @: "@"
    └── dominio
        ├── nombre: "company"
        ├── .: "."
        └── extensión: "com"
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Union


@dataclass
class SyntaxNode:
    """Nodo del árbol sintáctico."""

    label: str                     # Nombre del nodo / componente
    value: Optional[str] = None    # Valor terminal (None para nodos internos)
    children: List["SyntaxNode"] = field(default_factory=list)
    is_terminal: bool = False

    def add_child(self, child: "SyntaxNode") -> None:
        self.children.append(child)

    def to_string(self, indent: int = 0, last: bool = True) -> str:
        """Representación visual tipo árbol con pipes."""
        prefix = "    " * indent
        connector = "└── " if last else "├── "
        if indent == 0:
            line = f"{self.label}"
        else:
            val = f": {self.value!r}" if self.value is not None else ""
            line = f"{prefix}{connector}{self.label}{val}"

        lines = [line]
        for i, child in enumerate(self.children):
            is_last = (i == len(self.children) - 1)
            lines.append(child.to_string(indent + 1, is_last))
        return "\n".join(lines)

    def __repr__(self) -> str:  # pragma: no cover
        return f"SyntaxNode({self.label!r}, children={len(self.children)})"


class SyntaxTree:
    """
    Árbol sintáctico completo para un token.

    Construido a partir del diccionario `syntax_tree` devuelto
    por cada validador.
    """

    def __init__(self, root: SyntaxNode) -> None:
        self.root = root

    @classmethod
    def from_dict(cls, data: dict) -> "SyntaxTree":
        """Crea un SyntaxTree a partir del dict del validador."""
        root = _build_node("", data)
        return cls(root)

    def display(self) -> str:
        """Retorna la representación en texto del árbol."""
        return self.root.to_string()

    def __str__(self) -> str:
        return self.display()


def _build_node(label: str, value: Union[dict, str, int, bool, None]) -> SyntaxNode:
    if isinstance(value, dict):
        node = SyntaxNode(label=label or "ÁRBOL")
        items = list(value.items())
        for k, v in items:
            child = _build_node(str(k), v)
            node.add_child(child)
        return node
    else:
        return SyntaxNode(
            label=label,
            value=str(value) if value is not None else "",
            is_terminal=True,
        )
