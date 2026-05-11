"""
Exportación de resultados del análisis a TXT y CSV.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import List

from lexical.token_types import Token


class Exporter:
    """Exporta tokens a distintos formatos de archivo."""

    @staticmethod
    def to_txt(tokens: List[Token], filepath: str, source_text: str = "") -> None:
        """Exporta los tokens en formato texto legible."""
        lines = [
            "=" * 60,
            "REPORTE DE ANÁLISIS LÉXICO Y SINTÁCTICO",
            f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
        ]
        if source_text:
            lines += [
                "TEXTO ANALIZADO:",
                "-" * 40,
                source_text[:500] + ("..." if len(source_text) > 500 else ""),
                "",
            ]

        lines += [
            "TOKENS ENCONTRADOS:",
            "-" * 40,
        ]

        for i, tok in enumerate(tokens, 1):
            estado = "VÁLIDO" if tok.is_valid else "INVÁLIDO"
            lines.append(
                f"[{i:>3}] {tok.type.label():<12}  {tok.value:<35}  "
                f"Pos:{tok.start}-{tok.end}  {estado}"
            )
            if not tok.is_valid and tok.details.get("errors"):
                for err in tok.details["errors"]:
                    lines.append(f"       ↳ {err}")

        valid = sum(1 for t in tokens if t.is_valid)
        invalid = len(tokens) - valid
        lines += [
            "",
            "ESTADÍSTICAS:",
            "-" * 40,
            f"Total tokens: {len(tokens)}",
            f"  Válidos:    {valid}",
            f"  Inválidos:  {invalid}",
            "",
            "=" * 60,
        ]

        Path(filepath).write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def to_csv(tokens: List[Token], filepath: str) -> None:
        """Exporta los tokens a CSV para análisis en Excel u otros."""
        fieldnames = [
            "índice", "tipo", "valor", "inicio", "fin",
            "longitud", "línea", "columna", "es_válido", "errores",
        ]
        with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for i, tok in enumerate(tokens, 1):
                writer.writerow({
                    "índice":   i,
                    "tipo":     tok.type.label(),
                    "valor":    tok.value,
                    "inicio":   tok.start,
                    "fin":      tok.end,
                    "longitud": tok.length,
                    "línea":    tok.line,
                    "columna":  tok.column,
                    "es_válido": "Sí" if tok.is_valid else "No",
                    "errores":  "; ".join(tok.details.get("errors", [])),
                })

    @staticmethod
    def to_json(tokens: List[Token], filepath: str) -> None:
        """Exporta los tokens a JSON."""
        data = []
        for tok in tokens:
            data.append({
                "tipo": tok.type.label(),
                "valor": tok.value,
                "inicio": tok.start,
                "fin": tok.end,
                "es_válido": tok.is_valid,
                "línea": tok.line,
                "columna": tok.column,
                "errores": tok.details.get("errors", []),
                "componentes": tok.details.get("components", {}),
            })
        Path(filepath).write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )
