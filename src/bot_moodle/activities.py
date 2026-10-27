"""Extraccion de actividades: vistas de seccion + paginas de detalle assign.

Identidad de la actividad (D1): el cmid sale de la fuente autoritativa del DOM,
nunca del parametro `id` de `course/view.php`, que es el del **curso**.
Orden: `data-id` / `id="module-N"` del `li.activity-wrapper` -> `mod/*/view.php?id=`
en un anchor del contenedor -> ancla `course/view.php?...#module-N` -> descarte.
"""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_MODULE_ID_RE = re.compile(r"^module-(\d+)$")
_MOD_URL_RE = re.compile(r"/mod/[^/?#]+/view\.php\?[^\s#]*\bid=(\d+)")
_FRAGMENT_MODULE_RE = re.compile(r"#module-(\d+)")
_BODY_CMID_RE = re.compile(r"(?:^|\s)cmid-(\d+)(?:\s|$)")


def _modtype(li) -> str:
    for cls in li.get("class") or []:
        if cls.startswith("modtype_"):
            return cls[len("modtype_"):]
    return ""


def _dom_cmid(li) -> str:
    """Fuente 1: lo que el propio contenedor dice del course module."""
    data_id = (li.get("data-id") or "").strip()
    if data_id.isdigit():
        return data_id
    m = _MODULE_ID_RE.match((li.get("id") or "").strip())
    return m.group(1) if m else ""


def _resolve_cmid(li) -> tuple[str, str]:
    """Devuelve (cmid, href) por la prioridad de fuentes de D1.

    El href es el anchor del que salio el cmid y se usa como URL de detalle:
    una actividad sin URL de detalle utilizable se descarta (no hay a que
    pedirle la fecha). Un `modtype_label` cae aca, no tiene pagina propia.
    """
    hrefs = [a.get("href", "") for a in li.select("a[href]")]

    cmid = _dom_cmid(li)  # fuente 1: data-id / id="module-N"
    if cmid:
        for h in hrefs:
            if _MOD_URL_RE.search(h):
                return cmid, h
        for h in hrefs:
            if _FRAGMENT_MODULE_RE.search(h):
                return cmid, h
        return "", ""

    for h in hrefs:  # fuente 2: mod/*/view.php?id=
        m = _MOD_URL_RE.search(h)
        if m:
            return m.group(1), h
    for h in hrefs:  # fuente 3: ancla course/view.php?...#module-N
        m = _FRAGMENT_MODULE_RE.search(h)
        if m:
            return m.group(1), h
    return "", ""  # fuente 4: sin identidad determinable


def extract_activities(section_html: str, on_discard=None) -> list[dict]:
    """Extrae actividades con link de una vista de seccion.

    Salta wrappers sin identidad determinable (caso Yacomo isrestricted,
    etiquetas sueltas, contenedores sin `data-id` ni link a `mod/*`).
    Si se pasa `on_discard(act, motivo)`, cada wrapper descartado se reporta
    con motivo `sin_id` para que el descarte no sea silencioso (D2).
    Devuelve [{id, title, modtype, url}].
    """
    soup = BeautifulSoup(section_html, "lxml")
    found: list[dict] = []
    for li in soup.select("li.activity-wrapper"):
        cmid, href = _resolve_cmid(li)
        inst = li.select_one("span.instancename")
        named = li.select_one("div[data-activityname]")
        title = (
            inst.get_text(" ", strip=True)
            if inst and inst.get_text(strip=True)
            else (named.get("data-activityname", "").strip() if named else "")
        )
        if not cmid:
            if on_discard is not None:
                on_discard({"id": "", "title": title, "modtype": _modtype(li)}, "sin_id")
            continue
        if not title:
            anchor = li.select_one(f'a[href="{href}"]')
            title = anchor.get_text(" ", strip=True) if anchor else ""
        found.append({"id": cmid, "title": title, "modtype": _modtype(li), "url": href})
    return found


def _detail_cmid(detail_html: str, url: str) -> str:
    """cmid del detalle: DOM primero, despues la URL (nunca `course/view.php?id=`)."""
    soup = BeautifulSoup(detail_html, "lxml")
    body = soup.body
    if body is not None:
        m = _BODY_CMID_RE.search(" ".join(body.get("class") or []))
        if m:
            return m.group(1)
    m = _MOD_URL_RE.search(url or "")
    if m:
        return m.group(1)
    m = _FRAGMENT_MODULE_RE.search(url or "")
    if m:
        return m.group(1)
    return ""


def extract_activity_from_detail(detail_html: str, url: str) -> dict:
    """Extrae la actividad desde su pagina de detalle assign (breadcrumb/titulo)."""
    soup = BeautifulSoup(detail_html, "lxml")
    crumbs = [li.get_text(" ", strip=True) for li in soup.select("ol.breadcrumb li")]
    title = crumbs[-1] if crumbs else ""
    if not title and soup.title:
        title = soup.title.get_text(" ", strip=True).split("|")[0].split(":")[-1].strip()
    return {"id": _detail_cmid(detail_html, url), "title": title, "modtype": "assign", "url": url}