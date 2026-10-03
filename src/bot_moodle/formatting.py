"""Plantilla del mensaje: orden fijo, fecha corta ES, encabezados, sin links."""

from __future__ import annotations

from datetime import datetime

from bot_moodle.grouping import group_candidates

COURSE_ORDER = ["Programación", "BD2", "Inglés"]

_COURSE_ALIASES = {
    "prog3a26": "Programación",
    "programacion": "Programación",
    "programación": "Programación",
    "bases de datos ii": "BD2",
    "bd2": "BD2",
    "ingles": "Inglés",
    "inglés": "Inglés",
}

_DIAS = ["lun", "mar", "mié", "jue", "vie", "sáb", "dom"]
_MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sept", "oct", "nov", "dic"]

EMPTY_NOTICE = "Sin entregas con vencimiento hasta la semana que viene, atento a cambios"


def normalize_course(name: str) -> str:
    key = (name or "").strip().lower()
    for alias, canon in _COURSE_ALIASES.items():
        if alias in key:
            return canon
    return (name or "").strip()


def short_date(due: datetime, ref: datetime | None = None) -> str:
    """vie 10 oct, 23:59 (ano solo si cambia respecto a ref)."""
    base = f"{_DIAS[due.weekday()]} {due.day} {_MESES[due.month - 1]}, {due.hour:02d}:{due.minute:02d}"
    if ref is not None and due.year != ref.year:
        base = f"{_DIAS[due.weekday()]} {due.day} {_MESES[due.month - 1]} {due.year}, {due.hour:02d}:{due.minute:02d}"
    return base


def header_date(run: datetime) -> str:
    return f"{_DIAS[run.weekday()]} {run.day} {_MESES[run.month - 1]}"


def _ordered(candidates: list[dict]) -> list[dict]:
    canon = []
    for c in candidates:
        c = dict(c)
        c["course"] = normalize_course(c.get("course", ""))
        canon.append(c)
    rank = {name: i for i, name in enumerate(COURSE_ORDER)}
    return sorted(canon, key=lambda c: (rank.get(c["course"], 99), c["due"]))


def _blocks(
    candidates: list[dict],
    ref: datetime,
    new_ids: set[str] | None = None,
    changed_ids: set[str] | None = None,
) -> list[str]:
    new_ids = new_ids or set()
    changed_ids = changed_ids or set()
    # normalizar curso antes de agrupar para que PROG3A26 caiga en Programación
    normed = []
    for c in candidates:
        c = dict(c)
        c["course"] = normalize_course(c.get("course", ""))
        normed.append(c)
    # ordenar global por curso fijo + fecha, reagrupando en ese orden
    ordered = sorted(normed, key=lambda c: (COURSE_ORDER.index(c["course"]) if c["course"] in COURSE_ORDER else 99, c["due"]))
    groups = group_candidates(ordered)
    groups.sort(key=lambda g: COURSE_ORDER.index(g["course"]) if g["course"] in COURSE_ORDER else 99)
    out: list[str] = []
    for g in groups:
        out.append(f"*{g['course']}*")
        for sec in g["sections"]:
            out.append(sec["title"])
            for ap in sec["apartados"]:
                if ap["title"]:
                    out.append(ap["title"])
                for item in sorted(ap["items"], key=lambda c: c["due"]):
                    if item["id"] in new_ids:
                        marca = " 🆕 NUEVA"
                    elif item["id"] in changed_ids:
                        marca = " 🔄 fecha de entrega modificada"
                    else:
                        marca = ""
                    out.append(f"- {item['title']} (Cierra: {short_date(item['due'], ref)}){marca}")
        out.append("")
    if out and out[-1] == "":
        out.pop()
    return out


def format_digest(candidates: list[dict], run_date: datetime) -> str:
    lines = [f"*Comisión 4 - Vencimientos ({header_date(run_date)})*", ""]
    lines.extend(_blocks(_ordered(candidates), run_date))
    return "\n".join(lines)


def format_update(
    candidates: list[dict], new_ids: set[str], changed_ids: set[str] | None = None
) -> str:
    changed_ids = changed_ids or set()
    total = len(set(new_ids) | set(changed_ids))
    if changed_ids:
        lines = [f"*Comisión 4 - Actualización: {total} entrega(s) actualizada(s)*", ""]
    else:
        lines = [f"*Comisión 4 - Actualización: {len(new_ids)} entrega(s) nueva(s)*", ""]
    ref = min((c["due"] for c in candidates), default=datetime.now())
    lines.extend(_blocks(_ordered(candidates), ref, set(new_ids), set(changed_ids)))
    return "\n".join(lines)


def format_empty(run_date: datetime) -> str:
    return f"*Comisión 4 - Vencimientos ({header_date(run_date)})*\n\n{EMPTY_NOTICE}"
