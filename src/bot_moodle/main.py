"""CLI: python -m bot_moodle.main [--once] [--dry-run] [--send-test].

Codigos de salida (para cron/systemd):
  0 = exito (corrida completa, scheduler activo o dry-run generado)
  1 = fallo de campus/envio (red, login, Evolution: reintentar o revisar)
  2 = error de configuracion (falta .env: NO reintentar sin corregir)
"""

from __future__ import annotations

import argparse
import logging
from datetime import datetime

from bot_moodle.config import from_env
from bot_moodle.cycle import run_cycle
from bot_moodle.scheduler import build_scheduler
from bot_moodle.scrape import collect_candidates, discover_sections
from bot_moodle.sender import EvolutionSender
from bot_moodle.session import login_all
from bot_moodle.state import StateStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("bot_moodle")

TARGETS = [
    {"campus": "C1", "course": "Inglés", "course_id": "743"},
    {"campus": "C1", "course": "BD2", "course_id": "723"},
    {"campus": "C2", "course": "Programación", "course_id": "14"},
]


def build_targets(sessions: dict, cfg) -> list[dict]:
    base = {"C1": cfg.campus_c1.base_url, "C2": cfg.campus_c2.base_url}
    targets = []
    for t in TARGETS:
        sess = sessions.get(t["campus"])
        if sess is None:
            logger.warning("%s sin sesion: curso %s omitido (parcial, no completo)", t["campus"], t["course"])
            continue
        try:
            secs = discover_sections(sess, base[t["campus"]], t["course_id"])
        except Exception as exc:
            logger.warning("no se pudieron listar secciones de %s: %s", t["course"], exc)
            continue

        targets.append({**t, "base_url": base[t["campus"]], "sections": secs})
    return targets


def tick(dry_run: bool = False, dest_jid: str | None = None) -> dict:
    cfg = from_env()
    results = login_all(cfg.campuses)
    sessions = {name: r.session for name, r in results.items() if r.ok}
    for name, r in results.items():
        if not r.ok:
            logger.warning("campus %s fallido: %s (se continua con el otro)", name, r.error)
    sender = EvolutionSender(cfg.evo.base_url, cfg.evo.api_key, dest_jid or cfg.evo.group_jid)
    store = StateStore("estado.json")
    targets = build_targets(sessions, cfg)
    now = datetime.now()
    return run_cycle(
        fetch=lambda: collect_candidates(sessions, targets),
        now=now,
        store=store,
        sender=sender,
        dry_run=dry_run,
        dest_jid=dest_jid,
    )


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI. Devuelve 0 ok, 1 campus/envio, 2 config."""
    parser = argparse.ArgumentParser(description="Bot Moodle -> WhatsApp")
    parser.add_argument("--once", action="store_true", help="una sola corrida y salir (para cron)")
    parser.add_argument("--dry-run", action="store_true", help="genera el texto sin enviar")
    parser.add_argument("--send-test", action="store_true", help="envia al grupo de prueba (TEST_GROUP_JID)")
    args = parser.parse_args(argv)

    try:
        if args.send_test:
            import os

            dest = os.environ.get("TEST_GROUP_JID", "")
            res = tick(dry_run=False, dest_jid=dest)
            print(res["kind"], "enviado:", res["sent"])
            return 0
        if args.once or args.dry_run:
            res = tick(dry_run=args.dry_run)
            print(res["kind"], "enviado:", res["sent"])
            if args.dry_run:
                print(res["text"])
            return 0
    except ValueError as exc:
        # Error de configuracion (.env incompleto): codigo 2, no reintentar.
        logger.error("configuracion invalida: %s", exc)
        return 2
    except Exception as exc:
        # Fallo de campus/red/envio: codigo 1.
        logger.error("corrida fallida: %s", exc)
        return 1
    sched = build_scheduler(lambda: tick())
    sched.start()
    print("scheduler 8:00/20:00 activo")
    try:
        import time

        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        sched.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
