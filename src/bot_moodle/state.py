"""Estado persistente por assign id: {visto, notificado_urgente, notificado_digest, cierre_base}."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path


def base_of(due: datetime) -> dict:
    """Clave de comparación (día, mes, hora, minuto); año ignorado."""
    return {"d": due.day, "m": due.month, "h": due.hour, "mi": due.minute}


def base_matches(base: dict | None, due: datetime) -> bool:
    if not base:
        return False
    cur = base_of(due)
    return all(base.get(k) == v for k, v in cur.items())


class StateStore:
    """Persiste avistajes y notificaciones por assign id en un JSON."""

    def __init__(self, path: str | Path = "estado.json"):
        self.path = Path(path)
        self._data: dict = {}
        if self.path.exists():
            try:
                self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self) -> None:
        """Escritura atomica: vuelca a estado.json.tmp y renombra (os.replace).

        Un corte a mitad de escritura solo puede dejar corrupto el .tmp;
        el path real conserva siempre su ultimo estado bueno.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(self.path.name + ".tmp")
        tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        os.replace(tmp, self.path)

    def is_new(self, assign_id: str) -> bool:
        return str(assign_id) not in self._data

    def mark_seen(self, assign_id: str, now: datetime, due: datetime | None = None) -> None:
        key = str(assign_id)
        entry = self._data.get(key, {})
        entry.setdefault("visto", now.isoformat())
        entry.setdefault("notificado_urgente", False)
        entry.setdefault("notificado_digest", False)
        if due is not None and not entry.get("cierre_base"):
            entry["cierre_base"] = base_of(due)
        self._data[key] = entry
        self._save()

    def get_base(self, assign_id: str) -> dict | None:
        return self._data.get(str(assign_id), {}).get("cierre_base")

    def set_base(self, assign_id: str, due: datetime) -> None:
        key = str(assign_id)
        entry = self._data.get(key, {})
        entry["cierre_base"] = base_of(due)
        self._data[key] = entry
        self._save()

    def mark_notified(self, assign_id: str, kind: str) -> None:
        """kind: 'urgente' o 'digest'."""
        key = str(assign_id)
        entry = self._data.get(key, {})
        entry[f"notificado_{kind}"] = True
        self._data[key] = entry
        self._save()

    def was_notified(self, assign_id: str, kind: str) -> bool:
        return bool(self._data.get(str(assign_id), {}).get(f"notificado_{kind}", False))
