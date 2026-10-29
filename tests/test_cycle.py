"""10.1: scheduler 8:00/20:00 (lunes digest + vigia), dry-run sin envios."""

import json
from datetime import datetime

from bot_moodle.cycle import run_cycle
from bot_moodle.state import StateStore

LUNES = datetime(2026, 10, 5, 8, 0)
MARTES = datetime(2026, 10, 6, 20, 0)


def _c(id_, due, course="BD2", title=None):
    return {
        "id": id_,
        "title": title or f"act {id_}",
        "due": due,
        "course": course,
        "section": "Unidad 4",
        "apartado": "Práctica 💻",
        "section_index": 1,
    }


class _Sender:
    def __init__(self):
        self.sent = []

    def send_text(self, text, jid=None, timeout=20):
        from bot_moodle.sender import SendResult

        self.sent.append(text)
        return SendResult(ok=True)


def test_lunes_digest_envia_y_marca(tmp_path):
    sender = _Sender()
    res = run_cycle(
        fetch=lambda: [_c("1", datetime(2026, 10, 8, 23, 59))],
        now=LUNES,
        store=StateStore(tmp_path / "e.json"),
        sender=sender,
        dry_run=False,
    )
    assert res["sent"] is True
    assert "Vencimientos" in sender.sent[0]


def test_sin_novedades_no_envia_nada(tmp_path):
    sender = _Sender()
    res = run_cycle(
        fetch=lambda: [_c("1", datetime(2026, 10, 8, 23, 59))],
        now=MARTES,
        store=StateStore(tmp_path / "e.json"),
        sender=sender,
        dry_run=False,
        seen_ids={"1"},
    )
    assert res["sent"] is False
    assert sender.sent == []


def test_martes_con_nueva_urgente_envia_actualizacion(tmp_path):
    sender = _Sender()
    res = run_cycle(
        fetch=lambda: [_c("9", datetime(2026, 10, 7, 23, 59))],
        now=MARTES,
        store=StateStore(tmp_path / "e.json"),
        sender=sender,
        dry_run=False,
    )
    assert res["sent"] is True
    assert "Actualización" in sender.sent[0]
    assert "🆕 NUEVA" in sender.sent[0]


def test_dry_run_nunca_envia(tmp_path):
    sender = _Sender()
    res = run_cycle(
        fetch=lambda: [_c("1", datetime(2026, 10, 8, 23, 59))],
        now=LUNES,
        store=StateStore(tmp_path / "e.json"),
        sender=sender,
        dry_run=True,
    )
    assert res["sent"] is False
    assert sender.sent == []
    assert "Vencimientos" in res["text"]  # el texto igual se genera


# --- D4: avistaje siempre, notificacion solo tras ok=True ---

MARTES_08 = datetime(2026, 10, 6, 8, 0)
MIERCOLES_08 = datetime(2026, 10, 7, 8, 0)
LUNES_SIGUIENTE = datetime(2026, 10, 12, 8, 0)


class _SenderGuion:
    """Sender con guion: cada envio consume un ok y queda registrado."""

    def __init__(self, *oks):
        self.oks = list(oks)
        self.sent = []

    def send_text(self, text, jid=None, timeout=20):
        from bot_moodle.sender import SendResult

        ok = self.oks.pop(0)
        self.sent.append(text)
        return SendResult(ok=ok)


def test_dos_corridas_consecutivas_la_segunda_es_silencio(tmp_path):
    """El bug de produccion: 08:00 y 20:00 del mismo dia, con recarga desde disco."""
    ruta = tmp_path / "e.json"
    cands = [_c("9", datetime(2026, 10, 7, 23, 59))]
    sender = _SenderGuion(True, True)

    primera = run_cycle(fetch=lambda: cands, now=MARTES_08, store=StateStore(ruta), sender=sender)
    assert primera["kind"] == "update"
    assert "🆕 NUEVA" in sender.sent[0]

    segunda = run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=sender)
    assert segunda == {"sent": False, "kind": "silence", "text": ""}
    assert len(sender.sent) == 1, f"un solo mensaje en el dia: {sender.sent}"


def test_estado_ausente_envia_igual(tmp_path):
    """Fail-open: perder el estado nunca silencia un aviso."""
    sender = _SenderGuion(True)
    res = run_cycle(
        fetch=lambda: [_c("9", datetime(2026, 10, 7, 23, 59))],
        now=MARTES,
        store=StateStore(tmp_path / "nunca-existio.json"),
        sender=sender,
    )
    assert res["sent"] is True
    assert res["kind"] == "update"
    assert len(sender.sent) == 1


def test_envio_fallido_no_marca_notificado_y_reintenta(tmp_path):
    ruta = tmp_path / "e.json"
    cands = [_c("9", datetime(2026, 10, 7, 23, 59))]

    store = StateStore(ruta)
    primera = run_cycle(fetch=lambda: cands, now=MARTES_08, store=store, sender=_SenderGuion(False))
    assert primera["sent"] is False
    assert store.was_notified("9", "urgente") is False, "sin ok=True no hay notificacion"

    exito = _SenderGuion(True)
    segunda = run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=exito)
    assert segunda["sent"] is True and segunda["kind"] == "update"
    assert exito.sent[0] == primera["text"], "el reintento repite el mismo aviso"
    assert StateStore(ruta).was_notified("9", "urgente") is True

    tercera = run_cycle(fetch=lambda: cands, now=MIERCOLES_08, store=StateStore(ruta),
                        sender=_SenderGuion())
    assert tercera["kind"] == "silence"


def test_envio_fallido_conserva_la_marca_nueva_en_el_reintento(tmp_path):
    ruta = tmp_path / "e.json"
    cands = [_c("9", datetime(2026, 10, 7, 23, 59))]
    run_cycle(fetch=lambda: cands, now=MARTES_08, store=StateStore(ruta), sender=_SenderGuion(False))

    exito = _SenderGuion(True)
    run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=exito)
    assert "🆕 NUEVA" in exito.sent[0], "el reintento sale con la marca original"
    assert "0 entrega(s) nueva(s)" not in exito.sent[0]


def test_cambio_de_fecha_fallido_reintenta_el_mismo_cambio(tmp_path):
    ruta = tmp_path / "e.json"
    store = StateStore(ruta)
    store.mark_seen("K", MARTES, datetime(2026, 10, 12, 23, 59))
    store.mark_notified("K", "urgente")
    nueva = datetime(2026, 10, 8, 23, 59)
    cands = [_c("K", nueva)]

    primera = run_cycle(fetch=lambda: cands, now=MARTES, store=store, sender=_SenderGuion(False))
    assert "fecha de entrega modificada" in primera["text"]
    assert store.get_base("K") == {"d": 12, "m": 10, "h": 23, "mi": 59}

    exito = _SenderGuion(True)
    run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=exito)
    assert "fecha de entrega modificada" in exito.sent[0]
    assert StateStore(ruta).get_base("K") == {"d": 8, "m": 10, "h": 23, "mi": 59}


def test_digest_fallido_no_genera_rafaga_de_nueva(tmp_path):
    ruta = tmp_path / "e.json"
    cands = [_c("7", datetime(2026, 10, 15, 23, 59))]

    lunes = run_cycle(fetch=lambda: cands, now=LUNES, store=StateStore(ruta),
                      sender=_SenderGuion(False))
    assert lunes["kind"] == "digest" and lunes["sent"] is False
    assert StateStore(ruta).is_new("7") is False, \
        "el avistaje del lunes se persiste aunque el envio falle"

    martes = _SenderGuion(True)
    segunda = run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=martes)
    # D8: el martes reintenta el digest completo, nunca una rafaga de 🆕.
    assert segunda["kind"] == "digest"
    assert len(martes.sent) == 1
    assert "🆕 NUEVA" not in martes.sent[0]
    assert StateStore(ruta).is_new("7") is False


def test_digest_fallido_no_marca_digest_ni_base_y_el_lunes_siguiente_sale_igual(tmp_path):
    ruta = tmp_path / "e.json"
    cands = [_c("7", datetime(2026, 10, 15, 23, 59))]

    store = StateStore(ruta)
    run_cycle(fetch=lambda: cands, now=LUNES, store=store, sender=_SenderGuion(False))
    assert store.was_notified("7", "digest") is False
    assert store.get_base("7") is None, "la base del digest solo se sincroniza tras ok=True"

    exito = _SenderGuion(True)
    lunes2 = run_cycle(fetch=lambda: cands, now=LUNES_SIGUIENTE, store=StateStore(ruta),
                       sender=exito)
    assert lunes2["kind"] == "digest"
    assert "15" in exito.sent[0], "el digest se recompone de la ventana, no del estado"
    assert "🆕 NUEVA" not in exito.sent[0]


def test_reintento_del_digest_incluye_una_entrega_nueva_del_martes_sin_duplicar(tmp_path):
    """(i) lo que aparece despues del fallo entra en el reintento, una sola vez."""
    ruta = tmp_path / "e.json"
    lejos = _c("7", datetime(2026, 10, 15, 23, 59), title="lejos")
    cerca = _c("8", datetime(2026, 10, 8, 23, 59), title="cerca")

    run_cycle(fetch=lambda: [lejos], now=LUNES, store=StateStore(ruta), sender=_SenderGuion(False))

    martes = _SenderGuion(True)
    res = run_cycle(fetch=lambda: [lejos, cerca], now=MARTES, store=StateStore(ruta), sender=martes)
    assert res["kind"] == "digest"
    assert len(martes.sent) == 1, f"un solo envio por corrida: {martes.sent}"
    texto = martes.sent[0]
    assert texto.count("lejos") == 1 and texto.count("cerca") == 1
    assert "🆕 NUEVA" not in texto
    assert "entrega(s) nueva(s)" not in texto
    assert StateStore(ruta).digest_pendiente is False


# --- D8: si el digest falla, la corrida siguiente lo reintenta entero ---


def test_digest_fallido_deja_el_flag_digest_pendiente(tmp_path):
    """(a) flag persistido + avistaje igual (4.6/4.7 intactos)."""
    ruta = tmp_path / "e.json"
    cands = [_c("7", datetime(2026, 10, 15, 23, 59))]

    res = run_cycle(fetch=lambda: cands, now=LUNES, store=StateStore(ruta),
                    sender=_SenderGuion(False))
    assert res["kind"] == "digest" and res["sent"] is False

    assert StateStore(ruta).digest_pendiente is True
    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert data["__meta__"] == {"digest_pendiente": True}
    store = StateStore(ruta)
    assert store.is_new("7") is False, "el avistaje del digest sigue siendo incondicional"
    assert store.was_notified("7", "digest") is False
    assert store.get_base("7") is None


def test_digest_pendiente_se_reintenta_el_martes_como_digest(tmp_path):
    """(b)(c)(h) martes: digest completo, un solo envio, sin 🆕, y flag limpio."""
    ruta = tmp_path / "e.json"
    cands = [_c("7", datetime(2026, 10, 15, 23, 59))]
    run_cycle(fetch=lambda: cands, now=LUNES, store=StateStore(ruta), sender=_SenderGuion(False))

    martes = _SenderGuion(True)
    res = run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=martes)
    assert res["kind"] == "digest"
    assert len(martes.sent) == 1, f"un solo envio por corrida: {martes.sent}"
    lineas = martes.sent[0].splitlines()
    assert lineas[0].startswith("*Comisión 4 - Vencimientos ("), "encabezado de digest"
    assert "act 7" in martes.sent[0], "el digest se recompone de la ventana, no del estado"
    assert "🆕 NUEVA" not in martes.sent[0]

    store = StateStore(ruta)
    assert store.digest_pendiente is False
    assert "__meta__" not in json.loads(ruta.read_text(encoding="utf-8"))
    assert store.was_notified("7", "digest") is True

    # Same day 20:00: ya no hay digest pendiente -> silencio, sigue habiendo un solo envio.
    tarde = _SenderGuion()
    cuarta = run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=tarde)
    assert cuarta["kind"] == "silence"
    assert tarde.sent == []
    assert len(martes.sent) == 1


def test_reintento_fallido_mantiene_el_flag_para_la_corrida_siguiente(tmp_path):
    """(d) el reintento tambien falla: el flag sigue encendido."""
    ruta = tmp_path / "e.json"
    cands = [_c("7", datetime(2026, 10, 15, 23, 59))]
    run_cycle(fetch=lambda: cands, now=LUNES, store=StateStore(ruta), sender=_SenderGuion(False))

    martes = _SenderGuion(False)
    segundo = run_cycle(fetch=lambda: cands, now=MARTES, store=StateStore(ruta), sender=martes)
    assert segundo["kind"] == "digest" and len(martes.sent) == 1
    assert StateStore(ruta).digest_pendiente is True

    miercoles = _SenderGuion(True)
    tercero = run_cycle(fetch=lambda: cands, now=MIERCOLES_08, store=StateStore(ruta),
                        sender=miercoles)
    assert tercero["kind"] == "digest" and len(miercoles.sent) == 1, \
        "cada corrida programada reintenta una vez, sin bucle dentro de la corrida"
    assert StateStore(ruta).digest_pendiente is False


def test_digest_exitoso_del_lunes_no_deja_flag(tmp_path):
    """(e) el camino feliz no escribe __meta__."""
    ruta = tmp_path / "e.json"
    cands = [_c("7", datetime(2026, 10, 15, 23, 59))]

    res = run_cycle(fetch=lambda: cands, now=LUNES, store=StateStore(ruta),
                    sender=_SenderGuion(True))
    assert res["sent"] is True and res["kind"] == "digest"
    assert StateStore(ruta).digest_pendiente is False
    assert "__meta__" not in json.loads(ruta.read_text(encoding="utf-8"))


def test_digest_fallido_en_dry_run_no_enciende_el_flag(tmp_path):
    """(f) dry_run equivale a envio exitoso, como en el resto del change."""
    ruta = tmp_path / "e.json"
    sender = _SenderGuion()  # sin guion: si enviara, IndexError
    res = run_cycle(
        fetch=lambda: [_c("7", datetime(2026, 10, 15, 23, 59))],
        now=LUNES,
        store=StateStore(ruta),
        sender=sender,
        dry_run=True,
    )
    assert res["sent"] is False and res["kind"] == "digest"
    assert sender.sent == []
    assert StateStore(ruta).digest_pendiente is False


def test_reintento_con_ventana_vacia_manda_el_aviso_de_vacio_y_limpia_el_flag(tmp_path):
    """Triangulacion: digest vacio fallido -> el archivo queda solo con __meta__."""
    ruta = tmp_path / "e.json"
    run_cycle(fetch=lambda: [], now=LUNES, store=StateStore(ruta), sender=_SenderGuion(False))
    assert StateStore(ruta).digest_pendiente is True
    assert list(json.loads(ruta.read_text(encoding="utf-8"))) == ["__meta__"]

    martes = _SenderGuion(True)
    res = run_cycle(fetch=lambda: [], now=MARTES, store=StateStore(ruta), sender=martes)
    assert res["kind"] == "digest"
    assert len(martes.sent) == 1
    assert martes.sent[0].startswith("*Comisión 4 - Vencimientos (")
    assert StateStore(ruta).digest_pendiente is False


def test_tras_el_reintento_el_vigia_vuelve_a_su_ritmo(tmp_path):
    """Triangulacion: el flag no se queda pegado ni tapa una urgente del mismo dia."""
    ruta = tmp_path / "e.json"
    lejos = _c("7", datetime(2026, 10, 15, 23, 59), title="lejos")
    cerca = _c("8", datetime(2026, 10, 8, 23, 59), title="cerca")
    run_cycle(fetch=lambda: [lejos], now=LUNES, store=StateStore(ruta), sender=_SenderGuion(False))

    manana = _SenderGuion(True)
    run_cycle(fetch=lambda: [lejos], now=MARTES_08, store=StateStore(ruta), sender=manana)
    assert StateStore(ruta).digest_pendiente is False

    noche = _SenderGuion(True)
    res = run_cycle(fetch=lambda: [lejos, cerca], now=MARTES, store=StateStore(ruta), sender=noche)
    assert res["kind"] == "update"
    assert len(noche.sent) == 1
    assert "🆕 NUEVA" in next(l for l in noche.sent[0].splitlines() if "cerca" in l)


def test_envio_fallido_y_urgente_nueva_se_juntan_en_un_solo_reenvio(tmp_path):
    """Triangulacion: lo pendiente y lo nuevo salen en un unico mensaje."""
    ruta = tmp_path / "e.json"
    vieja = _c("9", datetime(2026, 10, 7, 23, 59), title="vieja")
    nueva = _c("10", datetime(2026, 10, 8, 23, 59), title="recien subida")

    run_cycle(fetch=lambda: [vieja], now=MARTES_08, store=StateStore(ruta),
              sender=_SenderGuion(False))

    reenvio = _SenderGuion(True)
    res = run_cycle(fetch=lambda: [vieja, nueva], now=MARTES, store=StateStore(ruta),
                    sender=reenvio)
    assert res["kind"] == "update"
    assert len(reenvio.sent) == 1, f"un solo envio por corrida: {reenvio.sent}"
    assert "vieja" in reenvio.sent[0] and "recien subida" in reenvio.sent[0]
    assert reenvio.sent[0].count("🆕 NUEVA") == 2

    cuarta = run_cycle(fetch=lambda: [vieja, nueva], now=MIERCOLES_08,
                       store=StateStore(ruta), sender=_SenderGuion())
    assert cuarta["kind"] == "silence"


def test_secretos_solo_desde_env(monkeypatch):
    import os

    from bot_moodle import config as cfg

    for k in ("MOODLE_C1_USER", "MOODLE_C1_PASS", "MOODLE_C2_USER", "MOODLE_C2_PASS", "EVO_API_KEY", "GROUP_JID"):
        monkeypatch.delenv(k, raising=False)
    try:
        cfg.from_env()
        assert False, "debió fallar sin env vars"
    except ValueError:
        pass
    monkeypatch.setenv("MOODLE_C1_USER", "u1")
    monkeypatch.setenv("MOODLE_C1_PASS", "p")
    monkeypatch.setenv("MOODLE_C2_USER", "u2")
    monkeypatch.setenv("MOODLE_C2_PASS", "p")
    monkeypatch.setenv("EVO_API_KEY", "k")
    monkeypatch.setenv("GROUP_JID", "g@g.us")
    assert cfg.from_env().campus_c1.username == "u1"
