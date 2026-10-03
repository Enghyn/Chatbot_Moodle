"""date-change-watch 1.1 (RED): cierre_base + migración silenciosa."""

import json
from datetime import datetime

from bot_moodle.state import StateStore

NOW = datetime(2026, 10, 6, 20, 0)
DUE = datetime(2026, 10, 9, 23, 59)


def test_guard_cierre_base_en_mark_seen(tmp_path):
    store = StateStore(tmp_path / "e.json")
    store.mark_seen("A1", NOW, DUE)
    data = json.loads((tmp_path / "e.json").read_text(encoding="utf-8"))
    assert data["A1"]["cierre_base"] == {"d": 9, "m": 10, "h": 23, "mi": 59}


def test_migracion_estado_viejo_adopta_base_sin_alertar(tmp_path):
    import json as _json

    from bot_moodle.watcher import select_urgent

    p = tmp_path / "e.json"
    # estado viejo: sin cierre_base, ya notificado como urgente
    p.write_text(
        _json.dumps({"V1": {"visto": NOW.isoformat(), "notificado_urgente": True, "notificado_digest": False}}),
        encoding="utf-8",
    )
    store = StateStore(p)
    assert store.get_base("V1") is None
    urg = select_urgent([{"id": "V1", "title": "vieja", "due": DUE}], store, NOW)
    assert urg == []  # silencio: migración no dispara aviso
    assert store.get_base("V1") == {"d": 9, "m": 10, "h": 23, "mi": 59}
    assert store.is_new("V1") is False


def test_set_base_sobrescribe_tras_reaviso(tmp_path):
    store = StateStore(tmp_path / "e.json")
    store.mark_seen("B1", NOW, DUE)
    nuevo = datetime(2026, 10, 12, 8, 30)
    store.set_base("B1", nuevo)
    assert store.get_base("B1") == {"d": 12, "m": 10, "h": 8, "mi": 30}


def test_doc_estado_describe_cierre_base_y_migracion():
    from pathlib import Path

    doc = Path(__file__).resolve().parent.parent / "docs" / "estado.md"
    assert doc.exists(), "falta docs/estado.md"
    texto = doc.read_text(encoding="utf-8").lower()
    assert "cierre_base" in texto
    assert "migración" in texto or "migracion" in texto
    assert "d" in texto and "mi" in texto  # formato día/mes/hora/minuto


# --- 2.1 (RED): comparación contra la base ignorando el año ---

def _known(store, aid, base_due, notified=True):
    store.mark_seen(aid, NOW, base_due)
    if notified:
        store.mark_notified(aid, "urgente")
    return store


def test_cambia_dia_reavisa(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    urg = select_urgent([{"id": "K", "title": "k", "due": datetime(2026, 10, 7, 23, 59)}], store, NOW)
    assert [c["id"] for c in urg] == ["K"]


def test_cambia_hora_reavisa(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    urg = select_urgent([{"id": "K", "title": "k", "due": datetime(2026, 10, 9, 8, 0)}], store, NOW)
    assert [c["id"] for c in urg] == ["K"]


def test_cambia_solo_ano_silencio(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    urg = select_urgent([{"id": "K", "title": "k", "due": datetime(2027, 10, 9, 23, 59)}], store, NOW)
    assert urg == []


def test_sin_cambios_silencio(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    urg = select_urgent([{"id": "K", "title": "k", "due": datetime(2026, 10, 9, 23, 59)}], store, NOW)
    assert urg == []


# --- 2.2 (RED): margen del re-aviso + single-shot por cambio ---

def test_cambio_margen_amplio_no_alerta(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    urg = select_urgent([{"id": "K", "title": "k", "due": datetime(2026, 10, 20, 23, 59)}], store, NOW)
    assert urg == []


def test_cambio_al_limite_7_dias_alerta(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 20, 23, 59))
    urg = select_urgent([{"id": "K", "title": "k", "due": datetime(2026, 10, 13, 23, 59)}], store, NOW)
    assert [c["id"] for c in urg] == ["K"]


def test_single_shot_no_repite_tras_actualizar_base(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    nuevo = datetime(2026, 10, 7, 23, 59)
    assert len(select_urgent([{"id": "K", "title": "k", "due": nuevo}], store, NOW)) == 1
    store.set_base("K", nuevo)  # el llamador actualiza tras envío exitoso
    assert select_urgent([{"id": "K", "title": "k", "due": nuevo}], store, NOW) == []


def test_segundo_cambio_distinto_vuelve_a_avis_arena(tmp_path):
    from bot_moodle.watcher import select_urgent

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    primero = datetime(2026, 10, 7, 23, 59)
    assert len(select_urgent([{"id": "K", "title": "k", "due": primero}], store, NOW)) == 1
    store.set_base("K", primero)
    segundo = datetime(2026, 10, 8, 12, 0)
    urg = select_urgent([{"id": "K", "title": "k", "due": segundo}], store, NOW)
    assert [c["id"] for c in urg] == ["K"]


# --- 3.1 (RED): marca fecha de entrega modificada, golden byte-a-byte ---

def _fc(id_, course, section, apartado, title, due):
    return {"id": id_, "course": course, "section": section, "apartado": apartado, "title": title, "due": due}


def test_golden_modificada_convive_con_nueva_y_digest():
    from bot_moodle.formatting import format_digest, format_update

    vie9 = datetime(2026, 10, 9, 23, 59)
    jue8 = datetime(2026, 10, 8, 23, 59)
    cands = [
        _fc("1384", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", "Entrega trabajo practico FastApi", vie9),
        _fc("1400", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", "TP nuevo 2prog4", jue8),
    ]
    texto = format_update(cands, {"1400"}, {"1384"})
    assert texto == (
        "*Comisión 4 - Actualización: 2 entrega(s) actualizada(s)*\n"
        "\n"
        "*Programación*\n"
        "UNIDAD 1: FASTAPI\n"
        "Práctica 💻\n"
        "- TP nuevo 2prog4 (Cierra: jue 8 oct, 23:59) 🆕 NUEVA\n"
        "- Entrega trabajo practico FastApi (Cierra: vie 9 oct, 23:59) 🔄 fecha de entrega modificada"
    )
    # el digest no lleva marcas
    digest = format_digest(cands, datetime(2026, 10, 5, 8, 0))
    assert "NUEVA" not in digest
    assert "modificada" not in digest


def test_golden_solo_modificada_sin_nuevas():
    from bot_moodle.formatting import format_update

    vie9 = datetime(2026, 10, 9, 23, 59)
    cands = [_fc("1384", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", "Entrega trabajo practico FastApi", vie9)]
    assert format_update(cands, set(), {"1384"}) == (
        "*Comisión 4 - Actualización: 1 entrega(s) actualizada(s)*\n"
        "\n"
        "*Programación*\n"
        "UNIDAD 1: FASTAPI\n"
        "Práctica 💻\n"
        "- Entrega trabajo practico FastApi (Cierra: vie 9 oct, 23:59) 🔄 fecha de entrega modificada"
    )


def test_compat_header_nuevas_sin_cambios():
    from bot_moodle.formatting import format_update

    vie9 = datetime(2026, 10, 9, 23, 59)
    cands = [_fc("1400", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", "TP nuevo", vie9)]
    assert format_update(cands, {"1400"}).startswith("*Comisión 4 - Actualización: 1 entrega(s) nueva(s)*")


# --- 3.2 (RED): corrida integrada dry-run con cambio simulado ---

TUESDAY = datetime(2026, 10, 6, 20, 0)
MONDAY = datetime(2026, 10, 12, 8, 0)


def _sender_ok():
    from bot_moodle.sender import SendResult

    class _S:
        def __init__(self):
            self.sent = []

        def send_text(self, text, jid=None, timeout=20):
            self.sent.append(text)
            return SendResult(ok=True)

    return _S()


def _full(id_, due, course="BD2"):
    return {
        "id": id_,
        "title": f"act {id_}",
        "due": due,
        "course": course,
        "section": "Unidad 4",
        "apartado": "Práctica 💻",
        "section_index": 1,
    }


def test_integrada_dry_run_reavisa_una_vez_y_actualiza_base(tmp_path):
    from bot_moodle.cycle import run_cycle

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    nuevo = datetime(2026, 10, 7, 23, 59)
    sender = _sender_ok()
    res = run_cycle(
        fetch=lambda: [_full("K", nuevo)],
        now=TUESDAY,
        store=store,
        sender=sender,
        dry_run=True,
    )
    assert "fecha de entrega modificada" in res["text"]
    assert "🆕" not in res["text"]
    assert store.get_base("K") == {"d": 7, "m": 10, "h": 23, "mi": 59}
    # segunda corrida con el mismo valor: silencio (single-shot)
    res2 = run_cycle(
        fetch=lambda: [_full("K", nuevo)],
        now=TUESDAY,
        store=store,
        sender=_sender_ok(),
        dry_run=True,
    )
    assert res2 == {"sent": False, "kind": "silence", "text": ""}


def test_integrada_margen_amplio_va_al_digest_y_actualiza_base(tmp_path):
    from bot_moodle.cycle import run_cycle

    store = StateStore(tmp_path / "e.json")
    _known(store, "K", datetime(2026, 10, 9, 23, 59))
    lejos = datetime(2026, 10, 25, 23, 59)
    res = run_cycle(
        fetch=lambda: [_full("K", lejos)],
        now=TUESDAY,
        store=store,
        sender=_sender_ok(),
        dry_run=True,
    )
    assert res["kind"] == "silence"  # sin alerta inmediata
    res_d = run_cycle(
        fetch=lambda: [_full("K", lejos)],
        now=MONDAY,
        store=store,
        sender=_sender_ok(),
        dry_run=True,
    )
    assert res_d["kind"] == "digest"
    assert "25" in res_d["text"]  # fecha actualizada visible
    assert store.get_base("K") == {"d": 25, "m": 10, "h": 23, "mi": 59}
