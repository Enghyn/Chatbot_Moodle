"""Filtro de comision: nombre + exclusion list, default inclusivo.

Ingles no se filtra (bypass). BD2 y Programacion: include-alias de la 4,
exclude-alias de otras, exclusion list por id/titulo exacto.
"""

from __future__ import annotations

import re

_INCLUDE = re.compile(r"comisi[oó]n\s*4|2prog4|com\s*4|\bc4\b", re.IGNORECASE)
_OTHER = re.compile(r"2prog3|y[aá]como|\bcom\s*1\b|com1", re.IGNORECASE)

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
    if _OTHER.search(title):
        return False
    return True  # sin marca: general, default inclusivo
