"""7.2: plantilla fija (Programacion > BD2 > Ingles), fecha corta, sin links."""

from datetime import datetime

from bot_moodle.formatting import (
    format_digest,
    format_empty,
    format_update,
    short_date,
)

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


def test_fecha_corta_sin_ano_y_con_ano_si_cambia():
    assert short_date(datetime(2026, 10, 10, 23, 59), ref=datetime(2026, 10, 6)) == "sáb 10 oct, 23:59"
    assert short_date(datetime(2027, 1, 5, 8, 0), ref=datetime(2026, 10, 6)) == "mar 5 ene 2027, 08:00"


def test_digest_byte_a_byte_orden_fijo_y_sin_links():
    cands = [
        _c("52527", "Inglés", "Class 5", "", "M2: Questionnaire #5 (Obligatory)", datetime(2026, 11, 2, 23, 59)),
        _c("56812", "BD2", "Unidad 4", "Práctica 💻", "Trabajo Práctico Unidad 4 (Semana 8)", datetime(2026, 10, 10, 23, 59)),
        _c("1384", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", "Entrega trabajo practico FastApi", datetime(2026, 10, 9, 23, 59)),
    ]
    assert format_digest(cands, LUN6) == (
        "*Comisión 4 - Vencimientos (lun 5 oct)*\n"
        "\n"
        "*Programación*\n"
        "UNIDAD 1: FASTAPI\n"
        "Práctica 💻\n"
        "- Entrega trabajo practico FastApi (Cierra: vie 9 oct, 23:59)\n"
        "\n"
        "*BD2*\n"
        "Unidad 4\n"
        "Práctica 💻\n"
        "- Trabajo Práctico Unidad 4 (Semana 8) (Cierra: sáb 10 oct, 23:59)\n"
        "\n"
        "*Inglés*\n"
        "Class 5\n"
        "- M2: Questionnaire #5 (Obligatory) (Cierra: lun 2 nov, 23:59)"
    )


def test_actualizacion_marca_solo_nuevas_con_contador():
    cands = [
        _c("1384", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", "Entrega trabajo practico FastApi", datetime(2026, 10, 9, 23, 59)),
        _c("1400", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", "TP nuevo 2prog4", datetime(2026, 10, 8, 23, 59)),
    ]
    assert format_update(cands, {"1400"}) == (
        "*Comisión 4 - Actualización: 1 entrega(s) nueva(s)*\n"
        "\n"
        "*Programación*\n"
        "UNIDAD 1: FASTAPI\n"
        "Práctica 💻\n"
        "- TP nuevo 2prog4 (Cierra: jue 8 oct, 23:59) 🆕 NUEVA\n"
        "- Entrega trabajo practico FastApi (Cierra: vie 9 oct, 23:59)"
    )


def test_semana_vacia_aviso_corto_y_sin_links():
    texto = format_empty(LUN6)
    assert texto == (
        "*Comisión 4 - Vencimientos (lun 5 oct)*\n"
        "\n"
        "Sin entregas con vencimiento hasta la semana que viene, atento a cambios"
    )
    assert "http" not in texto
