"""Ruta configurable de estado.json (TDD: RED primero, GREEN minimo)."""

import os

from bot_moodle.main import state_path


def test_default_es_estado_json_local(monkeypatch):
    monkeypatch.delenv("ESTADO_PATH", raising=False)
    assert state_path() == "estado.json"


def test_respeta_estado_path_configurado(monkeypatch):
    monkeypatch.setenv("ESTADO_PATH", "/data/estado.json")
    assert state_path() == "/data/estado.json"
    assert os.path.dirname(state_path()) == "/data"
