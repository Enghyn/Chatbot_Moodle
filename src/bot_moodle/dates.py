"""Parser de div[data-region=activity-dates]: alias ES + mapa de meses."""

from __future__ import annotations

import re
from datetime import datetime

from bs4 import BeautifulSoup

MESES = {
    "enero": 1, "ene": 1,
    "febrero": 2, "feb": 2,
    "marzo": 3, "mar": 3,
    "abril": 4, "abr": 4,
    "mayo": 5, "may": 5,
    "junio": 6, "jun": 6,
    "julio": 7, "jul": 7,
    "agosto": 8, "ago": 8,
    "septiembre": 9, "setiembre": 9, "sept": 9, "sep": 9, "set": 9,
    "octubre": 10, "oct": 10,
    "noviembre": 11, "nov": 11,
    "diciembre": 12, "dic": 12,
}

_INICIO = re.compile(r"apertura|abri[oó]|abre", re.IGNORECASE)
_FIN = re.compile(r"cierre|cierra|vence|fecha\s+(de\s+entrega|l[ií]mite)", re.IGNORECASE)
_FECHA = re.compile(
    r"(\d{1,2})\s+de\s+([a-záéíóúñ]+)\s+de\s+(\d{4})\s*,?\s*(\d{1,2}):(\d{2})",
    re.IGNORECASE,
)


def _parse_fecha_es(texto: str) -> datetime | None:
    m = _FECHA.search(texto)
    if not m:
        return None
    dia, mes_txt, anio, hora, minuto = m.groups()
    mes = MESES.get(mes_txt.lower())
    if not mes:
        return None
    return datetime(int(anio), mes, int(dia), int(hora), int(minuto))


def parse_activity_dates(detail_html: str) -> dict:
    """Devuelve {start, due} como datetime o None si no hay fecha parseable."""
    soup = BeautifulSoup(detail_html, "lxml")
    box = soup.select_one("div[data-region=activity-dates]")
    if box is None:
        return {"start": None, "due": None}
    start: datetime | None = None
    due: datetime | None = None
    # cada renglon suele ser <div><strong>Etiqueta:</strong> fecha</div>
    rows = box.select("div")
    texts = [r.get_text(" ", strip=True) for r in rows] if rows else [box.get_text(" ", strip=True)]
    for row in texts:
        fecha = _parse_fecha_es(row)
        if fecha is None:
            continue
        if _FIN.search(row):
            due = fecha
        elif _INICIO.search(row):
            start = fecha
    return {"start": start, "due": due}
