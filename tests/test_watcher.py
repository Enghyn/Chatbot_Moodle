"""8.2: umbral 7 dias + silencio sin novedades + alerta unica."""

from datetime import datetime

from bot_moodle.state import StateStore
from bot_moodle.watcher import select_urgent

NOW = datetime(2026, 9, 29, 8, 0)  # martes


def _c(id_, due):
    return {"id": id_, "title": f"act {id_}", "due": due}


def test_margen_1_alerta(tmp_path):
    store = StateStore(tmp_path / "e.json")
    urg = select_urgent([_c("a", datetime(2026, 9, 30, 23, 59))], store, NOW)
    assert [c["id"] for c in urg] == ["a"]


def test_margen_7_alerta(tmp_path):
    store = StateStore(tmp_path / "e.json")
    urg = select_urgent([_c("b", datetime(2026, 10, 6, 23, 59))], store, NOW)
    assert [c["id"] for c in urg] == ["b"]


def test_margen_10_espera_al_lunes(tmp_path):
    store = StateStore(tmp_path / "e.json")
    urg = select_urgent([_c("c", datetime(2026, 10, 9, 23, 59))], store, NOW)
    assert urg == []


def test_urgente_ya_alertada_no_se_re_alerta(tmp_path):
    store = StateStore(tmp_path / "e.json")
    cand = [_c("a", datetime(2026, 9, 30, 23, 59))]
    assert len(select_urgent(cand, store, NOW)) == 1
    store.mark_notified("a", "urgente")
    assert select_urgent(cand, store, NOW) == []
