"""Extraccion de actividades: vistas de seccion + paginas de detalle assign."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_ID_RE = re.compile(r"[?&]id=(\d+)")


def _modtype(li) -> str:
    for cls in li.get("class") or []:
        if cls.startswith("modtype_"):
            return cls[len("modtype_"):]
    return ""


def extract_activities(section_html: str) -> list[dict]:
    """Extrae actividades con link (id=) de una vista de seccion.

    Salta wrappers sin link (caso Yacomo isrestricted, etiquetas sueltas).
    Devuelve [{id, title, modtype, url}].
    """
    soup = BeautifulSoup(section_html, "lxml")
    found: list[dict] = []
    for li in soup.select("li.activity-wrapper"):
        link = None
        for a in li.select("a[href]"):
            if _ID_RE.search(a.get("href", "")):
                link = a
                break
        if link is None:
            continue
        href = link.get("href", "")
        m = _ID_RE.search(href)
        inst = li.select_one("span.instancename")
        named = li.select_one("div[data-activityname]")
        title = (
            inst.get_text(" ", strip=True)
            if inst and inst.get_text(strip=True)
            else (named.get("data-activityname", "").strip() if named else "")
        )
        if not title:
            title = link.get_text(" ", strip=True)
        found.append({"id": m.group(1), "title": title, "modtype": _modtype(li), "url": href})
    return found


def extract_activity_from_detail(detail_html: str, url: str) -> dict:
    """Extrae la actividad desde su pagina de detalle assign (breadcrumb/titulo)."""
    soup = BeautifulSoup(detail_html, "lxml")
    m = _ID_RE.search(url or "")
    crumbs = [li.get_text(" ", strip=True) for li in soup.select("ol.breadcrumb li")]
    title = crumbs[-1] if crumbs else ""
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True).split("|")[0].split(":")[-1].strip()
    return {"id": m.group(1) if m else "", "title": title, "modtype": "assign", "url": url}
