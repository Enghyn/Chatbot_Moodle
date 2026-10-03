"""Scheduler 8:00 y 20:00 diario (lunes 8:00 = digest + vigia)."""

from __future__ import annotations

from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger


def build_scheduler(tick: Callable[[], None]) -> BackgroundScheduler:
    """Dos jobs cron diarios; el modo (digest/vigia) lo decide la fecha en el tick."""
    sched = BackgroundScheduler()
    sched.add_job(tick, CronTrigger(hour=8, minute=0), id="manana")
    sched.add_job(tick, CronTrigger(hour=20, minute=0), id="noche")
    return sched
