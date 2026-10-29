"""Estado persistente por assign id: {visto, notificado_urgente, notificado_digest, cierre_base}.

Ademas guarda una clave reservada `__meta__` (nunca un assign id, que es
numerico) con los flags de la corrida, hoy `digest_pendiente`.
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

#: Accion operativa que declara el warning de carga: la corrida envia igual.
ACCION_ESTADO_NO_SANO = "arranca_con_estado_vacio_puede_renotificar"

#: Clave reservada de metadatos. Un `assign id` siempre es numerico, asi que
#: `"__meta__"` no puede colisionar con un registro.
META_KEY = "__meta__"

#: Flag de la corrida: el ultimo digest no salio y hay que reintentarlo entero.
FLAG_DIGEST_PENDIENTE = "digest_pendiente"


def _cargar(path: Path) -> tuple[dict, str, str]:
    """Clasifica la carga (D1): (datos, estado, motivo).

    `estado` es `ausente` | `vacio` | `corrupto` | `ok`; `motivo` es un token
    estable y greppable, vacio cuando el estado es sano. Nunca se loguea el
    contenido del archivo: ruta + motivo alcanzan para diagnosticar.
    """
    if not path.exists():
        return {}, "ausente", "archivo_inexistente"
    try:
        texto = path.read_text(encoding="utf-8")
    except OSError:
        return {}, "corrupto", "error_lectura"
    if not texto.strip():
        return {}, "vacio", "sin_contenido"
    try:
        data = json.loads(texto)
    except json.JSONDecodeError:
        return {}, "corrupto", "json_invalido"
    if not isinstance(data, dict):
        # `null`, `[]`, `"texto"`: decodifican pero no son registros; hoy
        # dejarian _data con ese valor y `is_new` reventaria con TypeError.
        return {}, "corrupto", "tipo_no_objeto"
    if not data:
        # Ningun camino del codigo escribe `{}`: solo puede venir de una
        # perdida o de una intervencion manual. Es `vacio`, no `ok`.
        return {}, "vacio", "objeto_sin_registros"
    return data, "ok", ""


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
        self._data, self._estado, self._motivo = _cargar(self.path)
        if self._estado != "ok":
            logger.warning(
                f"estado={self._estado} ruta={self.path} motivo={self._motivo} "
                f"accion={ACCION_ESTADO_NO_SANO}"
            )

    @property
    def estado(self) -> str:
        """Como arranco la corrida: `ausente` | `vacio` | `corrupto` | `ok`."""
        return self._estado

    def _save(self) -> None:
        """Escritura atomica con temporal unico por escritura + os.replace.

        Un corte a mitad de escritura solo puede dejar corrupto el .tmp;
        el path real conserva siempre su ultimo estado bueno. El nombre lleva
        pid y uuid4 para que dos escritores concurrentes nunca compartan el
        temporal. Si la publicacion falla, se borra el temporal **propio**;
        los temporales ajenos no se tocan (podrian ser una escritura viva).
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
        try:
            tmp.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
            os.replace(tmp, self.path)
        except Exception:
            tmp.unlink(missing_ok=True)
            raise

    def is_new(self, assign_id: str) -> bool:
        return str(assign_id) not in self._data

    @property
    def digest_pendiente(self) -> bool:
        """True si el ultimo digest no salio: la corrida siguiente lo reintenta.

        Tolerante a archivos previos a este flag (sin `__meta__`) y a un
        `__meta__` que no sea un objeto: en ambos casos vale `False`.
        """
        meta = self._data.get(META_KEY)
        if not isinstance(meta, dict):
            return False
        return bool(meta.get(FLAG_DIGEST_PENDIENTE, False))

    def _set_digest_pendiente(self, value: bool) -> None:
        """Persiste el flag; sin cambio observable no reescribe el archivo."""
        if self.digest_pendiente == value:
            return
        raw = self._data.get(META_KEY)
        meta = dict(raw) if isinstance(raw, dict) else {}
        if value:
            meta[FLAG_DIGEST_PENDIENTE] = True
            self._data[META_KEY] = meta
        else:
            meta.pop(FLAG_DIGEST_PENDIENTE, None)
            if meta:
                self._data[META_KEY] = meta
            else:
                # Sin flags no quedan metadatos: el archivo vuelve a su forma previa.
                self._data.pop(META_KEY, None)
        self._save()

    def mark_digest_pendiente(self) -> None:
        """El digest no salio: la proxima corrida lo reintenta completo."""
        self._set_digest_pendiente(True)

    def clear_digest_pendiente(self) -> None:
        """El digest salio: se apaga el flag de reintento."""
        self._set_digest_pendiente(False)

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
