"""8.2: umbral 7 dias + silencio sin novedades + alerta unica."""

import json
from datetime import datetime

from bot_moodle.state import StateStore
from bot_moodle.watcher import partition_urgent, select_urgent

NOW = datetime(2026, 9, 29, 8, 0)  # martes
BASE_VIEJA = {"d": 9, "m": 10, "h": 23, "mi": 59}


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


# --- D2/D3: el vigia persiste solo lo que NO va a enviar ---


def test_nueva_urgente_no_queda_vista_antes_de_enviar(tmp_path):
    """Si el envio falla, la corrida siguiente la tiene que volver a ver nueva."""
    store = StateStore(tmp_path / "e.json")
    nuevas, cambios = partition_urgent([_c("a", datetime(2026, 9, 30, 23, 59))], store, NOW)
    assert [c["id"] for c in nuevas] == ["a"]
    assert cambios == []
    assert store.is_new("a") is True, "el avistaje va despues de ok=True"


def test_nueva_fuera_de_margen_queda_vista_de_inmediato(tmp_path):
    """Comportamiento actual que no cambia: no se alerta al entrar en la ventana."""
    store = StateStore(tmp_path / "e.json")
    nuevas, cambios = partition_urgent([_c("c", datetime(2026, 10, 9, 23, 59))], store, NOW)
    assert nuevas == [] and cambios == []
    assert store.is_new("c") is False
    assert store.get_base("c") == BASE_VIEJA


def test_migracion_sin_base_sigue_silenciosa_y_vista(tmp_path):
    """Comportamiento actual que no cambia: un estado viejo adopta base sin alertar."""
    ruta = tmp_path / "e.json"
    ruta.write_text(
        json.dumps({"V1": {"visto": NOW.isoformat(), "notificado_urgente": True,
                           "notificado_digest": False}}),
        encoding="utf-8",
    )
    store = StateStore(ruta)
    nuevas, cambios = partition_urgent([_c("V1", datetime(2026, 10, 9, 23, 59))], store, NOW)
    assert nuevas == [] and cambios == []
    assert store.get_base("V1") == BASE_VIEJA
    assert store.is_new("V1") is False


def test_cambio_de_fecha_no_actualiza_base_antes_de_enviar(tmp_path):
    """La base la actualiza el ciclo tras ok=True, no el vigia."""
    store = StateStore(tmp_path / "e.json")
    store.mark_seen("K", NOW, datetime(2026, 10, 9, 23, 59))
    store.mark_notified("K", "urgente")
    nuevas, cambios = partition_urgent([_c("K", datetime(2026, 10, 2, 23, 59))], store, NOW)
    assert nuevas == []
    assert [c["id"] for c in cambios] == ["K"]
    assert store.get_base("K") == BASE_VIEJA, "la base vieja es lo que detecta el cambio"
    assert store.is_new("K") is False  # ya conocida: no sale con 🆕
