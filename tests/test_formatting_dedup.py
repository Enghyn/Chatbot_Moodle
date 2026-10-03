"""Dedup: si apartado == seccion, el encabezado sale una sola vez (bug real 2026-10-03)."""

from datetime import datetime

from bot_moodle.formatting import format_digest

LUN6 = datetime(2026, 10, 5, 8, 0)  # lunes 5 oct 2026


def _c(id_, course, section, apartado, title, due):
    return {
        "id": id_,
        "course": course,
        "section": section,
        "apartado": apartado,
        "title": title,
        "due": due,
    }


def test_apartado_igual_a_seccion_no_duplica_encabezado():
    cands = [
        _c("1", "Programación", "Práctica", "Práctica", "Entrega A", datetime(2026, 10, 9, 23, 59)),
    ]
    text = format_digest(cands, LUN6)
    assert text.count("Práctica") == 1


def test_apartado_distinto_de_seccion_muestra_ambos():
    cands = [
        _c("1", "Programación", "UNIDAD 1: FASTAPI", "Actividades", "Entrega A", datetime(2026, 10, 9, 23, 59)),
    ]
    text = format_digest(cands, LUN6)
    assert "UNIDAD 1: FASTAPI" in text
    assert "Actividades" in text
