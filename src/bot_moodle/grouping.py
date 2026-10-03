"""Agrupacion Curso > Seccion-verbatim > Apartado-verbatim (omite vacios)."""

from __future__ import annotations


def group_candidates(candidates: list[dict]) -> list[dict]:
    """Agrupa preservando orden de aparicion y nombres verbatim.

    Secciones claveadas por (index, title) para no colapsar duplicadas.
    Apartados/secciones sin items se omiten.
    Devuelve [{course, sections: [{index, title, apartados: [{title, items}]}]}].
    """
    courses: dict[str, dict] = {}
    order: list[str] = []
    for cand in candidates:
        course = cand.get("course", "")
        section = cand.get("section", "")
        apartado = cand.get("apartado", "")
        idx = cand.get("section_index", -1)
        if course not in courses:
            courses[course] = {"course": course, "sections": [], "_keys": {}}
            order.append(course)
        entry = courses[course]
        key = (idx, section)
        if key not in entry["_keys"]:
            entry["_keys"][key] = {"index": idx, "title": section, "apartados": [], "_names": {}}
            entry["sections"].append(entry["_keys"][key])
        sec = entry["_keys"][key]
        if apartado not in sec["_names"]:
            sec["_names"][apartado] = {"title": apartado, "items": []}
            sec["apartados"].append(sec["_names"][apartado])
        sec["_names"][apartado]["items"].append(cand)

    result = []
    for course in order:
        entry = courses[course]
        sections = []
        for sec in entry["sections"]:
            apartados = [a for a in sec["apartados"] if a["items"]]
            if not apartados:
                continue
            sections.append({"index": sec["index"], "title": sec["title"], "apartados": apartados})
        if not sections:
            continue
        result.append({"course": course, "sections": sections})
    return result
