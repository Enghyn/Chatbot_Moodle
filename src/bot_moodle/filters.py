"""Filtros temporal y de comision sobre candidatas con fecha."""

from __future__ import annotations

from datetime import datetime, timedelta

WINDOW_DAYS = 14


def drop_without_due(candidates: list[dict]) -> list[dict]:
    """Descarta en silencio las candidatas sin fecha fin (due None)."""
    return [c for c in candidates if c.get("due") is not None]


def in_window(due: datetime, now: datetime, days: int = WINDOW_DAYS) -> bool:
    """No vencida y dentro de la ventana de `days` desde hoy (dia de ejecucion)."""
    if due < now:
        return False
    return due <= now + timedelta(days=days)


def filter_window(candidates: list[dict], now: datetime, days: int = WINDOW_DAYS) -> list[dict]:
    """Solo no-vencidas en ventana, orden ascendente por fecha fin."""
    in_win = [c for c in drop_without_due(candidates) if in_window(c["due"], now, days)]
    return sorted(in_win, key=lambda c: c["due"])
