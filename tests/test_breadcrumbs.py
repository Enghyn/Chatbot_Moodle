"""3.3: breadcrumb curso + seccion/apartado verbatim (emojis incluidos)."""

from pathlib import Path

from bot_moodle.breadcrumbs import parse_breadcrumb

FIX = Path(__file__).parent / "fixtures"


def _html(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_bd2_breadcrumb_curso_y_practica_verbatim():
    crumb = parse_breadcrumb(_html("assign_bd2_tp_u4_56812.html"))
    assert crumb["course"] == "Bases de Datos II"
    assert crumb["section"] == "Práctica 💻"
    assert "Unidad 4" in crumb["activity"]


def test_uml_breadcrumb_actividades_con_cohete_verbatim():
    crumb = parse_breadcrumb(_html("assign_uml_1457.html"))
    assert crumb["course"] == "PROG3A26"
    assert crumb["section"] == "Actividades 🚀"
    assert "UML" in crumb["activity"]


def test_fastapi_breadcrumb_practica_verbatim():
    crumb = parse_breadcrumb(_html("assign_fastapi_1384.html"))
    assert crumb["course"] == "PROG3A26"
    assert crumb["section"] == "Práctica 💻"


def test_sin_breadcrumb_devuelve_vacios_sin_error():
    crumb = parse_breadcrumb("<html><body><p>sin miga</p></body></html>")
    assert crumb == {"course": "", "section": "", "activity": ""}
