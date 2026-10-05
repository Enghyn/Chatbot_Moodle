"""unit-section-headers 2.2: encabezado de una linea, goldens byte-a-byte.

Ejemplo real del operador: `CSS - Práctica`. Fallback sin padre: solo el
apartado, como antes del cambio.
"""

from datetime import datetime

from bot_moodle.formatting import format_digest

LUN6 = datetime(2026, 10, 5, 8, 0)  # lunes 5 oct 2026


def _c(id_, course, apartado, title, due, unidad_padre=None, section=""):
    return {
        "id": id_,
        "course": course,
        "section": section or apartado,
        "apartado": apartado,
        "unidad_padre": unidad_padre,
        "title": title,
        "due": due,
    }


def test_digest_encabezado_unidad_apartado_byte_a_byte():
    cands = [
        _c("52527", "Inglés", "Class 5", "M2: Questionnaire #5 (Obligatory)",
           datetime(2026, 11, 2, 23, 59), unidad_padre="Module 2: Personal Presentations"),
        _c("56812", "BD2", "Práctica 💻", "Trabajo Práctico Unidad 4 (Semana 8)",
           datetime(2026, 10, 10, 23, 59), unidad_padre="Unidad 4"),
        _c("1384", "Programación", "Práctica", "Entrega CSS Grid",
           datetime(2026, 10, 9, 23, 59), unidad_padre="CSS"),
    ]
    assert format_digest(cands, LUN6) == (
        "*Comisión 4 - Vencimientos (lun 5 oct)*\n"
        "\n"
        "*Programación*\n"
        "CSS - Práctica\n"
        "- Entrega CSS Grid (Cierra: vie 9 oct, 23:59)\n"
        "\n"
        "*BD2*\n"
        "Unidad 4 - Práctica 💻\n"
        "- Trabajo Práctico Unidad 4 (Semana 8) (Cierra: sáb 10 oct, 23:59)\n"
        "\n"
        "*Inglés*\n"
        "Module 2: Personal Presentations - Class 5\n"
        "- M2: Questionnaire #5 (Obligatory) (Cierra: lun 2 nov, 23:59)"
    )


def test_digest_fallback_sin_padre_apartado_solo():
    cands = [
        _c("1384", "Programación", "Práctica 💻", "Entrega sin padre",
           datetime(2026, 10, 9, 23, 59)),
    ]
    assert format_digest(cands, LUN6) == (
        "*Comisión 4 - Vencimientos (lun 5 oct)*\n"
        "\n"
        "*Programación*\n"
        "Práctica 💻\n"
        "- Entrega sin padre (Cierra: vie 9 oct, 23:59)"
    )
    assert "http" not in format_digest(cands, LUN6)
