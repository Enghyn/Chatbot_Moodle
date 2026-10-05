"""unit-section-headers 2.1: agrupacion Curso > `Unidad - Apartado` (una linea).

Clave = (unidad_padre o seccion-como-antes, apartado). Sin padre -> titulo
solo con el apartado (comportamiento anterior); padre == apartado -> una
sola linea (dedup vigente).
"""

from datetime import datetime

from bot_moodle.grouping import group_candidates, group_title


def _c(id_, course, apartado, due, unidad_padre=None, section=""):
    return {
        "id": id_,
        "title": f"act {id_}",
        "due": due,
        "course": course,
        "section": section,
        "apartado": apartado,
        "unidad_padre": unidad_padre,
        "section_index": 0,
    }


D1 = datetime(2026, 10, 8, 23, 59)
D2 = datetime(2026, 10, 10, 23, 59)


def test_dos_practicas_de_distintas_unidades_no_comparten_encabezado():
    cands = [
        _c("1", "BD2", "Práctica 💻", D2, unidad_padre="Unidad 4", section="Práctica 💻"),
        _c("2", "BD2", "Práctica 💻", D1, unidad_padre="Unidad 2", section="Práctica 💻"),
    ]
    groups = group_candidates(cands)
    titulos = [g["title"] for g in groups[0]["groups"]]
    assert titulos == ["Unidad 4 - Práctica 💻", "Unidad 2 - Práctica 💻"]


def test_misma_unidad_y_apartado_colapsan_en_un_grupo():
    cands = [
        _c("1", "Programación", "Práctica 💻", D1, unidad_padre="FastAPI"),
        _c("2", "Programación", "Práctica 💻", D2, unidad_padre="FastAPI"),
    ]
    groups = group_candidates(cands)
    assert [g["title"] for g in groups[0]["groups"]] == ["FastAPI - Práctica 💻"]
    assert len(groups[0]["groups"][0]["items"]) == 2


def test_sin_padre_fallback_a_apartado_solo_como_antes():
    cands = [_c("1", "BD2", "Práctica 💻", D1, section="Unidad 4")]
    groups = group_candidates(cands)
    assert [g["title"] for g in groups[0]["groups"]] == ["Práctica 💻"]


def test_padre_igual_a_apartado_no_duplica():
    assert group_title("Práctica", "Práctica") == "Práctica"
    assert group_title("Práctica", "PRÁCTICA") == "PRÁCTICA"  # verbatim, sin normalizar


def test_apartado_vacio_usa_padre_o_seccion():
    assert group_title("Module 2: Personal Presentations", "") == "Module 2: Personal Presentations"
    assert group_title(None, "", section="Class 5") == "Class 5"
    assert group_title("CSS", "Práctica") == "CSS - Práctica"


def test_entrada_vacia_devuelve_vacio():
    assert group_candidates([]) == []
