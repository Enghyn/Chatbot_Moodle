"""8.1: estado persistente por assign id en estado.json."""

import json
from datetime import datetime

from bot_moodle.state import StateStore

NOW = datetime(2026, 9, 29, 8, 0)


def test_id_nuevo_se_registra_con_timestamp(tmp_path):
    store = StateStore(tmp_path / "estado.json")
    assert store.is_new("56812") is True
    store.mark_seen("56812", NOW)
    data = json.loads((tmp_path / "estado.json").read_text(encoding="utf-8"))
    assert "56812" in data
    assert data["56812"]["visto"]  # timestamp presente


def test_id_conocido_no_se_retrata_como_nuevo(tmp_path):
    store = StateStore(tmp_path / "estado.json")
    store.mark_seen("56812", NOW)
    store2 = StateStore(tmp_path / "estado.json")  # recarga desde disco
    assert store2.is_new("56812") is False
    assert store2.is_new("1384") is True


def test_flags_digest_y_urgente_por_id(tmp_path):
    store = StateStore(tmp_path / "estado.json")
    store.mark_seen("1", NOW)
    assert store.was_notified("1", "urgente") is False
    store.mark_notified("1", "urgente")
    assert store.was_notified("1", "urgente") is True
    assert store.was_notified("1", "digest") is False
