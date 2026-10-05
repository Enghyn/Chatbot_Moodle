"""Scrape: curso -> secciones (indice) -> actividades -> detalle (fecha+breadcrumb)."""

from __future__ import annotations

import logging
from typing import Any

from bot_moodle.activities import extract_activities
from bot_moodle.breadcrumbs import parse_breadcrumb
from bot_moodle.dates import parse_activity_dates
from bot_moodle.sections import resolve_parent_unit

logger = logging.getLogger(__name__)


def section_url(base_url: str, course_id: str, index: int) -> str:
    return f"{base_url.rstrip('/')}/course/view.php?id={course_id}&section={index}"


def collect_candidates(sessions: dict[str, Any], targets: list[dict], timeout: int = 20) -> list[dict]:
    """Recorre las secciones indicadas de cada curso y devuelve candidatas con fecha.

    targets: [{campus, course_id, course, base_url, sections: [{index, title}]}].
    La seccion verbatim viene del indice recorrido; el apartado, del breadcrumb
    del detalle. Las actividades sin fecha se descartan en silencio.
    `unidad_padre` se deriva de `units` (tabs de unidad del curso, opcional):
    sin units -> None y la agrupacion usa el comportamiento anterior.
    """
    candidates: list[dict] = []
    for t in targets:
        sess = sessions.get(t["campus"])
        if sess is None:
            logger.warning("%s: sin sesion, se omite curso %s", t["campus"], t.get("course_id"))
            continue
        units = t.get("units", []) or []
        for sec in t.get("sections", []):
            idx = sec["index"] if isinstance(sec, dict) else sec
            sec_title = sec["title"] if isinstance(sec, dict) else t.get("section_fallback", "")
            try:
                resp = sess.get(section_url(t["base_url"], t["course_id"], idx), timeout=timeout)
            except Exception as exc:
                logger.warning("seccion %s/%s fallo: %s", t["course_id"], idx, exc)
                continue
            for act in extract_activities(resp.text or ""):
                try:
                    detail = sess.get(act["url"], timeout=timeout)
                except Exception as exc:
                    logger.warning("detalle %s fallo: %s", act["id"], exc)
                    continue
                parsed = parse_activity_dates(detail.text or "")
                if parsed["due"] is None:
                    continue  # sin fecha: descarte silencioso
                crumb = parse_breadcrumb(detail.text or "")
                candidates.append(
                    {
                        "id": act["id"],
                        "title": act["title"],
                        "due": parsed["due"],
                        "start": parsed["start"],
                        "course": t.get("course", ""),
                        "section": sec_title,
                        "apartado": crumb["section"],
                        "unidad_padre": resolve_parent_unit(units, idx),
                        "section_index": idx,
                        "url": act["url"],
                    }
                )
    return candidates


def _course_html(session: Any, base_url: str, course_id: str, timeout: int = 20) -> str:
    resp = session.get(section_url(base_url, course_id, 0), timeout=timeout)
    return resp.text or ""


def discover_sections(session: Any, base_url: str, course_id: str, timeout: int = 20) -> list[dict]:
    """Devuelve [{index, title, url}] con las secciones del curso via indice."""
    from bot_moodle.sections import enumerate_sections

    return [s for s in enumerate_sections(_course_html(session, base_url, course_id, timeout)) if s["index"] >= 0]


def discover_units(session: Any, base_url: str, course_id: str, timeout: int = 20) -> list[dict]:
    """Devuelve [{index, title}] con las tabs de unidad (padres de seccion)."""
    from bot_moodle.sections import extract_unit_tabs

    return extract_unit_tabs(_course_html(session, base_url, course_id, timeout))
