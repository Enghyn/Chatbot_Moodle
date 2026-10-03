"""6.1: filtro de comision por nombre + exclusion list (default inclusivo)."""

from bot_moodle.comision import should_include


def test_incluye_compartidas_con_la_4():
    assert should_include("TP Final COM4,COM3,COM1", "999", course="BD2") is True
    assert should_include("Entrega Com3 y Com4", "999", course="BD2") is True
    assert should_include("TP 2prog3 y 2prog4", "999", course="Programación") is True


def test_excluye_solo_otra_comision():
    assert should_include("TP 2prog3", "999", course="BD2") is False
    assert should_include("TP (Comisión Prof. Yácomo)", "999", course="BD2") is False
    assert should_include("Trabajo Com1", "999", course="Programación") is False


def test_sin_marca_incluye_por_defecto():
    assert should_include("Entrega trabajo practico FastApi", "1384", course="Programación") is True


def test_exclusion_list_por_id_y_titulo_exacto():
    assert should_include("Subir trabajo de UML a Java", "1457", course="Programación") is False
    # mismo titulo con otro id tambien se excluye (titulo exacto en lista)
    assert should_include("Subir trabajo de UML a Java", "9999", course="Programación") is False
