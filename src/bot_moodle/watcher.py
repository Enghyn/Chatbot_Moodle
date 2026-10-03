"""Vigia urgente: nuevas y cambios de fecha con margen <= 7 dias, una sola vez."""

from __future__ import annotations

from datetime import datetime

from bot_moodle.state import StateStore, base_matches

URGENT_DAYS = 7


def margin_days(due: datetime, now: datetime) -> int:
    return (due.date() - now.date()).days


def is_date_change(store: StateStore, assign_id: str, due: datetime) -> bool:
    """True si hay base y día/mes/hora difieren (año ignorado)."""
    base = store.get_base(assign_id)
    if base is None:
        return False
    return not base_matches(base, due)


def select_urgent(candidates: list[dict], store: StateStore, now: datetime) -> list[dict]:
    """Devuelve candidatas nuevas o con cambio de fecha a alertar en esta corrida.

    Registra avistajes (mark_seen) pero no actualiza la base ni marca
    notificacion: el llamador actualiza la base y marca 'urgente' tras el
    envio exitoso (alerta unica + single-shot por cambio).
    """
    new_urgent, changed_urgent = partition_urgent(candidates, store, now)
    return [*new_urgent, *changed_urgent]


def partition_urgent(
    candidates: list[dict], store: StateStore, now: datetime
) -> tuple[list[dict], list[dict]]:
    """Separa (nuevas urgentes, re-avisos por cambio con margen <= 7 días)."""
    new_urgent: list[dict] = []
    changed_urgent: list[dict] = []
    for cand in candidates:
        due = cand.get("due")
        if due is None or due < now:
            continue
        aid = str(cand.get("id", ""))
        is_new = store.is_new(aid)
        if is_new:
            store.mark_seen(aid, now, due)
            if margin_days(due, now) <= URGENT_DAYS and not store.was_notified(aid, "urgente"):
                new_urgent.append(cand)
            continue
        if store.get_base(aid) is None:
            # Migración: estado viejo sin cierre_base la adopta sin alertar.
            store.mark_seen(aid, now, due)
            continue
        if is_date_change(store, aid, due) and margin_days(due, now) <= URGENT_DAYS:
            changed_urgent.append(cand)
    return new_urgent, changed_urgent
