"""Ruta configurable de estado.json (TDD: RED primero, GREEN minimo)."""

import json
import os

from bot_moodle.main import state_path


def test_default_es_estado_json_local(monkeypatch):
    monkeypatch.delenv("ESTADO_PATH", raising=False)
    assert state_path() == "estado.json"


def test_respeta_estado_path_configurado(monkeypatch):
    monkeypatch.setenv("ESTADO_PATH", "/data/estado.json")
    assert state_path() == "/data/estado.json"
    assert os.path.dirname(state_path()) == "/data"


# --- D6: el cierre de corrida lleva el estado con el que se cargo el store ---


def _tick_con_dobles(monkeypatch, capturado, ruta_estado):
    """Sustituye todo lo externo de `tick` y captura el fetch del ciclo."""
    from bot_moodle import main as main_mod

    class _Evo:
        base_url = "https://evo.example"
        api_key = "dummy"
        group_jid = "grupo@g.us"
        instance = "instancia"

    class _Cfg:
        campuses = []
        evo = _Evo()

    def _run_cycle(*args, **kwargs):
        kwargs["fetch"]()  # ejecuta el fetch que arma main.tick
        return {"sent": False, "kind": "silence", "text": ""}

    def _collect(*args, **kwargs):
        capturado.update(kwargs)
        return []

    monkeypatch.setenv("ESTADO_PATH", str(ruta_estado))
    monkeypatch.setattr(main_mod, "from_env", lambda: _Cfg())
    monkeypatch.setattr(main_mod, "login_all", lambda campuses: {})
    monkeypatch.setattr(main_mod, "EvolutionSender", lambda *a, **kw: object())
    monkeypatch.setattr(main_mod, "build_targets", lambda sessions, cfg: [])
    monkeypatch.setattr(main_mod, "run_cycle", _run_cycle)
    monkeypatch.setattr(main_mod, "collect_candidates", _collect)
    return main_mod.tick()


def test_tick_pasa_el_estado_del_store_al_cierre(tmp_path, monkeypatch):
    capturado: dict = {}
    _tick_con_dobles(monkeypatch, capturado, tmp_path / "estado.json")
    assert capturado.get("estado") == "ausente"

    ruta = tmp_path / "estado.json"
    ruta.write_text(json.dumps({"1": {"visto": "2026-10-28T08:00:00"}}), encoding="utf-8")
    capturado.clear()
    _tick_con_dobles(monkeypatch, capturado, ruta)
    assert capturado.get("estado") == "ok"
