"""Enumeracion de secciones via indice del curso (drawer + tabs + select)."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_SECTION_RE = re.compile(r"[?&]section=(\d+)")
_MESSAGING_RE = re.compile(r"caj[oó]n de mensajer|mensajer|conversacion", re.IGNORECASE)

# Apartados genericos (prefijos, case-insensitive): solo para el fallback
# cuando la pagina no trae marcas de nivel tab_level_* en las tabs.
_GENERIC_PREFIXES = (
    "practica", "práctica",
    "actividades",
    "inicio",
    "autoevaluacion", "autoevaluación",
    "encuesta",
    "introduccion", "introducción",
)


def _is_generic_tab(title: str) -> bool:
    t = (title or "").strip().lower()
    return any(t.startswith(p) for p in _GENERIC_PREFIXES)


def extract_unit_tabs(course_html: str) -> list[dict]:
    """Tabs de unidad ordenadas por seccion: [{index, title}].

    Camino principal: tabs cuyo <li> trae la marca estructural
    `tab_level_0` del formato onetopic (nivel del arbol, no clase visual).
    Fallback (sin marcas de nivel): tabs con section>=0 cuyo titulo NO es
    un apartado generico, en orden de seccion. Excluye mensajeria.
    """
    soup = BeautifulSoup(course_html, "lxml")
    found: list[dict] = []
    saw_level = False
    for a in soup.select("a.nav-link[title]"):
        title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
        if not title or _MESSAGING_RE.search(title):
            continue
        href = a.get("href", "")
        m = _SECTION_RE.search(href)
        if m is None:
            continue
        li = a.find_parent("li")
        classes = li.get("class", []) if li is not None else []
        if any(str(c).startswith("tab_level_") for c in classes):
            saw_level = True
        level0 = "tab_level_0" in [str(c) for c in classes]
        found.append({"index": int(m.group(1)), "title": title, "level0": level0})
    if saw_level:
        units = [ {"index": t["index"], "title": t["title"]}
                  for t in found if t["level0"] ]
    else:
        units = [ {"index": t["index"], "title": t["title"]}
                  for t in found if not _is_generic_tab(t["title"]) ]
    units.sort(key=lambda u: u["index"])
    return units


def resolve_parent_unit(unit_tabs: list[dict], section_index: int) -> str | None:
    """Unidad padre de una seccion: tab de unidad con mayor section <= index.

    Las tabs hijas (nivel 1: Practica, Class N...) nunca son padres entre si;
    el orden es por numero de seccion, no por posicion en el DOM (el DOM
    mezcla ambos niveles). Sin candidato -> None (formato anterior).
    """
    if section_index is None or section_index < 0:
        return None
    best: dict | None = None
    for u in unit_tabs or []:
        idx = u.get("index", -1)
        if idx < 0 or idx > section_index:
            continue
        if best is None or idx > best["index"]:
            best = u
    return best["title"] if best else None


def _clean_index_title(text: str) -> str:
    text = re.sub(r"^\s*Expandir\s+Colapsar\s+", "", text).strip()
    text = re.sub(r"\s+Destacado\s*$", "", text).strip()
    return text


def enumerate_sections(course_html: str, base_url: str = "", course_id: str = "") -> list[dict]:
    """Devuelve [{index, title, url}] con TODAS las secciones del curso.

    Prioridad: <option value=...section=N> (tabs-tree) > a.nav-link[title]
    (drawer, excluye mensajeria) > .courseindex-section-title.
    """
    soup = BeautifulSoup(course_html, "lxml")
    sections: list[dict] = []

    for opt in soup.select("option[value]"):
        value = opt.get("value", "")
        m = _SECTION_RE.search(value)
        if not m:
            continue
        title = opt.get_text(strip=True)
        if not title:
            continue
        url = value if value.startswith("http") else urljoin(base_url + "/", value.lstrip("/")) if base_url else value
        sections.append({"index": int(m.group(1)), "title": title, "url": url})
    if sections:
        return sections

    for a in soup.select("a.nav-link[title]"):
        title = (a.get("title") or a.get_text(" ", strip=True) or "").strip()
        if not title or _MESSAGING_RE.search(title):
            continue
        href = a.get("href", "")
        m = _SECTION_RE.search(href)
        if href and not m and "course" not in href and "section" not in href:
            continue
        url = href if href.startswith("http") else urljoin(base_url + "/", href.lstrip("/")) if base_url and href else href
        sections.append({"index": int(m.group(1)) if m else -1, "title": title, "url": url})
    if sections:
        return sections

    for el in soup.select(".courseindex-section-title"):
        title = _clean_index_title(el.get_text(" ", strip=True))
        if not title:
            continue
        sections.append({"index": -1, "title": title, "url": ""})
    return sections
