"""4.1: parser de activity-dates con alias ES por campus."""

from datetime import datetime
from pathlib import Path

from bot_moodle.dates import parse_activity_dates

FIX = Path(__file__).parent / "fixtures"


def test_ingles_abrio_cierra_a_datetime():
    parsed = parse_activity_dates((FIX / "tema_ingles_class5.html").read_text(encoding="utf-8"))
    assert parsed["due"] == datetime(2026, 11, 2, 23, 59)
    assert parsed["start"] == datetime(2026, 9, 8, 8, 30)


def test_uml_apertura_cierre_a_datetime():
    parsed = parse_activity_dates((FIX / "assign_uml_1457.html").read_text(encoding="utf-8"))
    assert parsed["due"] == datetime(2026, 8, 25, 0, 0)
    assert parsed["start"] == datetime(2026, 8, 18, 0, 0)


def test_alias_vence_y_fecha_limite_son_fin():
    assert parse_activity_dates("<div data-region='activity-dates'>Vence: viernes, 10 de octubre de 2026, 23:59</div>")[
        "due"
    ] == datetime(2026, 10, 10, 23, 59)
    assert parse_activity_dates(
        "<div data-region='activity-dates'>Fecha límite: viernes, 10 de octubre de 2026, 23:59</div>"
    )["due"] == datetime(2026, 10, 10, 23, 59)


def test_alias_fecha_de_entrega_y_abre():
    parsed = parse_activity_dates(
        "<div data-region='activity-dates'>"
        "<div>Abre: lunes, 5 de octubre de 2026, 08:00</div>"
        "<div>Fecha de entrega: viernes, 10 de octubre de 2026, 23:59</div>"
        "</div>"
    )
    assert parsed["start"] == datetime(2026, 10, 5, 8, 0)
    assert parsed["due"] == datetime(2026, 10, 10, 23, 59)
