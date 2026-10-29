"""1.2 deploy-go-live: escritura atomica de estado.json (tmp + rename).

Un corte a mitad de escritura NUNCA debe dejar JSON corrupto en el
path real: el corte cae sobre el .tmp y el target conserva su ultimo
estado bueno.
"""

import json
import re
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


# --- Temporal unico por escritura (D5): dos escritores no comparten .tmp ---

NOMBRE_TMP = re.compile(r"^estado\.json\.\d+\.[0-9a-f]{32}\.tmp$")


def test_tmp_tiene_pid_y_uuid_y_es_unico_por_escritura(tmp_path, monkeypatch):
    """Nombra el temporal que cada publicacion intenta renombrar."""
    import os

    origenes: list[str] = []
    real_replace = os.replace

    def _espia(src, dst):
        origenes.append(Path(src).name)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", _espia)
    store = StateStore(tmp_path / "estado.json")
    store.mark_seen("1", NOW)
    store.mark_seen("2", NOW)

    assert len(origenes) == 2, f"una publicacion por mark_seen: {origenes}"
    for nombre in origenes:
        assert NOMBRE_TMP.match(nombre), f"el temporal no es estado.json.<pid>.<uuid>.tmp: {nombre}"
        assert str(os.getpid()) in nombre, f"el pid identifica al proceso: {nombre}"
    assert origenes[0] != origenes[1], f"dos escrituras no comparten temporal: {origenes}"


def test_temporal_ajeno_no_se_pisa(tmp_path, monkeypatch):
    """Un temporal de otro proceso queda intacto byte a byte."""
    import os

    ajeno = tmp_path / "estado.json.99999.deadbeef.tmp"
    basura = b"\x00basura de otro proceso\xff"
    ajeno.write_bytes(basura)

    publicados: list[str] = []
    real_replace = os.replace

    def _espia(src, dst):
        publicados.append(Path(src).name)
        return real_replace(src, dst)

    monkeypatch.setattr(os, "replace", _espia)
    StateStore(tmp_path / "estado.json").mark_seen("1", NOW)

    assert publicados and publicados[0] != ajeno.name, \
        f"la escritura usa su propio temporal, no el ajeno: {publicados}"
    assert NOMBRE_TMP.match(publicados[0]), \
        f"el temporal propio es unico (pid + uuid): {publicados[0]}"
    assert ajeno.read_bytes() == basura, "la escritura propia no puede tocar el temporal ajeno"
    data = json.loads((tmp_path / "estado.json").read_text(encoding="utf-8"))
    assert "1" in data and data["1"]["visto"] == NOW.isoformat()


def test_temporal_propio_se_borra_si_falla_la_publicacion(tmp_path, monkeypatch):
    """Si os.replace falla, el temporal que se acaba de escribir no queda huerfano."""
    import os

    target = tmp_path / "estado.json"
    _write_good(target)

    intentos: list[Path] = []

    def _boom(src, dst):
        intentos.append(Path(src))
        raise OSError("fallo de publicacion simulado")

    store = StateStore(target)
    monkeypatch.setattr(os, "replace", _boom)
    with pytest.raises(OSError):
        store.mark_seen("99999", NOW)

    assert len(intentos) == 1, f"una unica publicacion intentada: {intentos}"
    propio = intentos[0]
    assert not propio.exists(), f"el temporal propio se borra: {propio.name}"
    assert json.loads(target.read_text(encoding="utf-8")) == GOOD


def test_temporal_propio_se_borra_si_falla_el_write(tmp_path, monkeypatch):
    """El otro camino de error: el corte cae mientras se escribe el temporal."""
    target = tmp_path / "estado.json"
    _write_good(target)
    real_write_text = Path.write_text

    def _corta(self, data, *args, **kwargs):
        if self.suffix == ".tmp":
            real_write_text(self, str(data)[: 10], *args, **kwargs)
            raise OSError("corte simulado durante el write")
        return real_write_text(self, data, *args, **kwargs)

    monkeypatch.setattr(Path, "write_text", _corta)
    store = StateStore(target)
    with pytest.raises(OSError):
        store.mark_seen("99999", NOW)
    assert [p.name for p in tmp_path.iterdir() if p.suffix == ".tmp"] == []
    assert json.loads(target.read_text(encoding="utf-8")) == GOOD
