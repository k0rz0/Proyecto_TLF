"""
Historial de validaciones recientes.

Persiste las últimas N validaciones en un archivo JSON local.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

_HISTORY_FILE = Path(__file__).parent.parent / ".history.json"
_MAX_ENTRIES  = 100


@dataclass
class HistoryEntry:
    timestamp: str
    input_type: str   # "TEXT", "FORM", "SIMULATOR"
    value: str
    token_type: str
    is_valid: bool
    errors: List[str]


class HistoryManager:
    """Gestiona el historial de validaciones."""

    def __init__(self, max_entries: int = _MAX_ENTRIES) -> None:
        self._max = max_entries
        self._entries: List[HistoryEntry] = []
        self._load()

    def add(
        self,
        value: str,
        token_type: str,
        is_valid: bool,
        errors: Optional[List[str]] = None,
        input_type: str = "FORM",
    ) -> None:
        entry = HistoryEntry(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            input_type=input_type,
            value=value,
            token_type=token_type,
            is_valid=is_valid,
            errors=errors or [],
        )
        self._entries.insert(0, entry)
        if len(self._entries) > self._max:
            self._entries = self._entries[: self._max]
        self._save()

    def get_recent(self, n: int = 20) -> List[HistoryEntry]:
        return self._entries[:n]

    def clear(self) -> None:
        self._entries = []
        self._save()

    # ------------------------------------------------------------------

    def _load(self) -> None:
        if not _HISTORY_FILE.exists():
            return
        try:
            raw = json.loads(_HISTORY_FILE.read_text(encoding="utf-8"))
            self._entries = [HistoryEntry(**r) for r in raw]
        except Exception:
            self._entries = []

    def _save(self) -> None:
        try:
            _HISTORY_FILE.write_text(
                json.dumps([asdict(e) for e in self._entries], ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception:
            pass  # No bloquear la app si el historial no se puede guardar
