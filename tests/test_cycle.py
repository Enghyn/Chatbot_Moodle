"""10.1: scheduler 8:00/20:00 (lunes digest + vigia), dry-run sin envios."""

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
