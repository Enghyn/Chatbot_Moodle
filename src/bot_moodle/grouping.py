"""Agrupacion Curso > `Unidad - Apartado` en una sola linea (omite vacios)."""

from __future__ import annotations


def group_title(unidad_padre: str | None, apartado: str | None, section: str = "") -> str:
    """Titulo de grupo: `{Unidad} - {Apartado}`; fallbacks sin romper.

    Sin padre -> solo el apartado (comportamiento anterior); padre igual
    al apartado (case-insensitive) -> una sola linea (dedup); sin apartado
    -> padre o, en ultima instancia, la seccion verbatim.
    """
    up = (unidad_padre or "").strip()
    ap = (apartado or "").strip()
    if up and ap and up.lower() != ap.lower():
        return f"{up} - {ap}"
    return ap or up or (section or "").strip()


def group_candidates(candidates: list[dict]) -> list[dict]:
    """Agrupa por Curso > `Unidad - Apartado` preservando orden de aparicion.

    La clave es (unidad_padre o seccion, apartado): sin `unidad_padre`
    (datos viejos o seccion huerfana) cae al comportamiento anterior y
    los grupos sin items se omiten.
    Devuelve [{course, groups: [{title, items}]}].
    """
    courses: dict[str, dict] = {}
    order: list[str] = []
    for cand in candidates:
        course = cand.get("course", "")
        section = cand.get("section", "")
        apartado = cand.get("apartado", "")
        parent = (cand.get("unidad_padre") or "").strip() or section
        if course not in courses:
            courses[course] = {"course": course, "groups": [], "_keys": {}}
            order.append(course)
        entry = courses[course]
        key = (parent, apartado)
        if key not in entry["_keys"]:
            entry["_keys"][key] = {
                "title": group_title(cand.get("unidad_padre"), apartado, section),
                "items": [],
            }
            entry["groups"].append(entry["_keys"][key])
        entry["_keys"][key]["items"].append(cand)

    result = []
    for course in order:
        groups = [g for g in courses[course]["groups"] if g["items"]]
        if not groups:
            continue
        result.append({"course": course, "groups": groups})
    return result
