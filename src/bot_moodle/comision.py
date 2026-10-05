"""Filtro de comision: nombre + exclusion list, default inclusivo.

Ingles no se filtra (bypass). BD2 y Programacion: include-alias de la 4,
exclude-alias de otras, exclusion list por id/titulo exacto.
"""

from __future__ import annotations

import re

_INCLUDE = re.compile(r"comisi[oó]n\s*4|2prog4|com\s*4|\bc4\b", re.IGNORECASE)
_OTHER = re.compile(r"2prog3|y[aá]como|\bcom\s*1\b|com1", re.IGNORECASE)

# Apellidos (y nombres) de profesores de comision 4. Solo se evaluan tras
# "prof" en contexto de comision, para no chocar con palabras comunes
# ("espejo", "torres" sueltos no significan nada).
_PROF_MENTION = re.compile(r"prof\.?\s*[:\-]?\s*([a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+){0,2})", re.IGNORECASE)
_PROF_COMISION = re.compile(r"comisi[oó]n", re.IGNORECASE)
_OURS = frozenset({"neira", "sergio", "buccella", "farias", "farías", "espejo", "giuliano", "torres", "matias"})

EXCLUDED_IDS = frozenset({"1457"})
EXCLUDED_TITLES = frozenset({"Subir trabajo de UML a Java"})

_ENGLISH = {"ingles", "inglés"}


def is_english(course: str) -> bool:
    return (course or "").strip().lower() in _ENGLISH


def should_include(title: str, assign_id: str, course: str = "") -> bool:
    """True si la actividad entra al mensaje para nuestra comision (4)."""
    if is_english(course):
        return True
    if str(assign_id) in EXCLUDED_IDS:
        return False
    if (title or "").strip() in EXCLUDED_TITLES:
        return False
    title = title or ""
    if _INCLUDE.search(title):
        return True
    if _PROF_COMISION.search(title):
        tokens = [w.lower() for m in _PROF_MENTION.finditer(title) for w in m.group(1).split()]
        if tokens:
            return any(t in _OURS for t in tokens)
    if _OTHER.search(title):
        return False
    return True  # sin marca: general, default inclusivo
