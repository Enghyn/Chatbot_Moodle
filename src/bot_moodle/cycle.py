"""Ciclo diario: digest lunes 8:00, vigia 8:00/20:00, silencio sin novedades."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Optional

from bot_moodle.comision import should_include
from bot_moodle.filters import drop_without_due, filter_window
from bot_moodle.formatting import format_digest, format_empty, format_update
from bot_moodle.state import StateStore
from bot_moodle.watcher import partition_urgent


def apply_filters(candidates: list[dict], now: datetime) -> list[dict]:
    """Tuberia completa: con-fecha -> comision -> ventana 14d ordenada."""
    with_due = drop_without_due(candidates)
    admitted = [c for c in with_due if should_include(c.get("title", ""), str(c.get("id", "")), c.get("course", ""))]
    return filter_window(admitted, now)


def run_cycle(
    fetch: Callable[[], list[dict]],
    now: datetime,
    store: StateStore,
    sender: Any,
    dry_run: bool = False,
    seen_ids: Optional[set[str]] = None,
    dest_jid: Optional[str] = None,
) -> dict:
    """Ejecuta una corrida. Devuelve {sent, kind, text}."""
    for aid in seen_ids or set():
        if store.is_new(str(aid)):
            store.mark_seen(str(aid), now)
    candidates = apply_filters(fetch(), now)

    if now.weekday() == 0:  # lunes: digest (+ vigia integrado)
        text = format_digest(candidates, now) if candidates else format_empty(now)
        kind = "digest"
        notify_kind = "digest"
        new_ids: set[str] = set()
    else:
        new_urgent, changed_urgent = partition_urgent(candidates, store, now)
        if not new_urgent and not changed_urgent:
            return {"sent": False, "kind": "silence", "text": ""}
        new_ids = {str(c["id"]) for c in new_urgent}
        changed_ids = {str(c["id"]) for c in changed_urgent}
        text = format_update(candidates, new_ids, changed_ids)
        kind = "update"
        notify_kind = "urgente"

    sent = False
    if not dry_run:
        result = sender.send_text(text, jid=dest_jid) if dest_jid else sender.send_text(text)
        sent = bool(result.ok)
    if sent or dry_run:
        for c in candidates:
            store.mark_seen(str(c["id"]), now, c.get("due"))
        if kind == "digest":
            for c in candidates:
                store.mark_notified(str(c["id"]), "digest")
                if c.get("due") is not None:
                    # La fecha actualizada sale en el digest: base sincronizada.
                    store.set_base(str(c["id"]), c["due"])
        else:
            for aid in new_ids | changed_ids:
                store.mark_notified(aid, "urgente")
            by_id = {str(c["id"]): c for c in candidates}
            for aid in changed_ids:
                # Single-shot por cambio: base solo tras envío exitoso.
                if by_id[aid].get("due") is not None:
                    store.set_base(aid, by_id[aid]["due"])
    return {"sent": sent, "kind": kind, "text": text}
