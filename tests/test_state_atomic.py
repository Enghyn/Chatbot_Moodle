"""1.2 deploy-go-live: escritura atomica de estado.json (tmp + rename).

Un corte a mitad de escritura NUNCA debe dejar JSON corrupto en el
path real: el corte cae sobre el .tmp y el target conserva su ultimo
estado bueno.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from bot_moodle.state import StateStore

NOW = datetime(2026, 9, 29, 8, 0)

GOOD = {"56812": {"visto": NOW.isoformat(), "notificado_urgente": False, "notificado_digest": False}}


def _write_good(path: Path) -> None:
    path.write_text(json.dumps(GOOD, ensure_ascii=False, indent=2), encoding="utf-8")


def test_corte_entre_write_y_rename_conserva_json_bueno(tmp_path, monkeypatch):
    """Falla inyectada en os.replace: el target conserva el JSON bueno previo."""
    import os

    target = tmp_path / "estado.json"
    _write_good(target)

    def _boom(src, dst):
        raise OSError("corte simulado: caida entre write y rename")

    monkeypatch.setattr(os, "replace", _boom)
    store = StateStore(target)
    assert store.is_new("56812") is False  # estado previo cargado
    with pytest.raises(OSError):
        store.mark_seen("99999", NOW)
    # El target sigue siendo JSON valido con los datos previos intactos.
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == GOOD


def test_corte_a_mitad_de_write_no_corrompe_target(tmp_path, monkeypatch):
    """Write truncado a mitad de camino: el target conserva el JSON bueno previo."""
    target = tmp_path / "estado.json"
    _write_good(target)

    real_write_text = Path.write_text

    def _truncated(self, data, *args, **kwargs):
        # Simula corte electrico: escribe la mitad y falla. Solo en el .tmp.
        if self.suffix == ".tmp":
            real_write_text(self, str(data)[: len(str(data)) // 2], *args, **kwargs)
            raise OSError("corte simulado: write a medias")
        return real_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _truncated)
    store = StateStore(target)
    with pytest.raises(OSError):
        store.mark_seen("99999", NOW)
    # El target sigue siendo JSON valido con los datos previos intactos.
    data = json.loads(target.read_text(encoding="utf-8"))
    assert data == GOOD
