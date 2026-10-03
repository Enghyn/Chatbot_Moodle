"""1.3 deploy-go-live: codigos de salida de main.py para cron/systemd.

0 = exito, 1 = fallo de campus/envio, 2 = error de configuracion.
"""

from bot_moodle import main as main_mod


def _ok_tick(**kwargs):
    return {"kind": "digest", "sent": True, "text": "hola"}


def test_exit_0_en_corrida_ok(monkeypatch):
    monkeypatch.setattr(main_mod, "tick", _ok_tick)
    assert main_mod.main(["--once"]) == 0


def test_exit_0_en_dry_run_ok(monkeypatch):
    monkeypatch.setattr(main_mod, "tick", _ok_tick)
    assert main_mod.main(["--once", "--dry-run"]) == 0


def test_exit_1_en_fallo_de_campus_o_red(monkeypatch):
    def _boom(**kwargs):
        raise RuntimeError("campus caido")

    monkeypatch.setattr(main_mod, "tick", _boom)
    assert main_mod.main(["--once"]) == 1


def test_exit_1_en_fallo_de_envio(monkeypatch):
    def _boom(**kwargs):
        raise ConnectionError("evolution no responde")

    monkeypatch.setattr(main_mod, "tick", _boom)
    assert main_mod.main(["--once"]) == 1


def test_exit_2_en_error_de_configuracion(monkeypatch):
    def _boom(**kwargs):
        raise ValueError("Falta variable de entorno requerida: GROUP_JID")

    monkeypatch.setattr(main_mod, "tick", _boom)
    assert main_mod.main(["--once"]) == 2
