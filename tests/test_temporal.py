"""5.1: ventana 14 dias + exclusion de vencidas + orden ascendente."""

from datetime import datetime

from bot_moodle.filters import filter_window

NOW = datetime(2026, 9, 29, 8, 0)


def _c(id_, due):
    return {"id": id_, "title": f"act {id_}", "due": due}


def test_incluye_3_dias_y_excluye_20_dias():
    cerca = _c("a", datetime(2026, 10, 2, 23, 59))  # +3 dias
    lejos = _c("b", datetime(2026, 10, 19, 23, 59))  # +20 dias
    result = filter_window([cerca, lejos], NOW)
    assert [c["id"] for c in result] == ["a"]


def test_excluye_uml_vencido_25_ago_evaluado_29_sept():
    uml = _c("1457", datetime(2026, 8, 25, 0, 0))
    assert filter_window([uml], NOW) == []


def test_ordena_3_candidatas_por_fecha_fin():
    c1 = _c("x", datetime(2026, 10, 10, 23, 59))
    c2 = _c("y", datetime(2026, 10, 2, 23, 59))
    c3 = _c("z", datetime(2026, 10, 5, 12, 0))
    assert [c["id"] for c in filter_window([c1, c2, c3], NOW)] == ["y", "z", "x"]


def test_borde_14_dias_entra_15_no():
    from datetime import timedelta

    en_borde = _c("b14", NOW + timedelta(days=14))
    fuera = _c("b15", NOW + timedelta(days=14, seconds=1))
    result = filter_window([en_borde, fuera], NOW)
    assert [c["id"] for c in result] == ["b14"]
