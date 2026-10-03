"""Breadcrumb de paginas de detalle: curso + seccion/apartado verbatim."""

from __future__ import annotations

from bs4 import BeautifulSoup


def parse_breadcrumb(detail_html: str) -> dict:
    """Devuelve {course, section, activity} tal cual aparecen (sin normalizar)."""
    soup = BeautifulSoup(detail_html, "lxml")
    items = [li.get_text(" ", strip=True) for li in soup.select("ol.breadcrumb li")]
    items = [t for t in items if t]
    if not items:
        return {"course": "", "section": "", "activity": ""}
    return {
        "course": items[0] if len(items) > 0 else "",
        "section": items[1] if len(items) > 1 else "",
        "activity": items[-1] if len(items) > 2 else "",
    }
