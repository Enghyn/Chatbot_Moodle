"""Enumeracion de secciones via indice del curso (drawer + tabs + select)."""

from __future__ import annotations

import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup

_SECTION_RE = re.compile(r"[?&]section=(\d+)")
_MESSAGING_RE = re.compile(r"caj[oó]n de mensajer|mensajer|conversacion", re.IGNORECASE)


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
