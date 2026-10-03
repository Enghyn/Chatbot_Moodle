"""7.1: agrupacion Curso > Seccion-verbatim > Apartado-verbatim, omite vacios."""

from bot_moodle.grouping import group_candidates


def _c(id_, course, section, apartado, idx=0):
    from datetime import datetime

    return {
        "id": id_,
        "title": f"act {id_}",
        "due": datetime(2026, 10, 2, 23, 59),
        "course": course,
        "section": section,
        "apartado": apartado,
        "section_index": idx,
    }


def test_apartado_sin_candidatas_no_muestra_encabezado():
    cands = [_c("1", "BD2", "Unidad 4", "Práctica 💻")]
    groups = group_candidates(cands)
    apartados = [a["title"] for s in groups[0]["sections"] for a in s["apartados"]]
    assert apartados == ["Práctica 💻"]
    assert "Actividades 🧩" not in apartados


def test_seccion_duplicada_se_muestra_tal_cual():
    cands = [
        _c("1", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", idx=2),
        _c("2", "Programación", "UNIDAD 1: FASTAPI", "Práctica 💻", idx=8),
    ]
    groups = group_candidates(cands)
    titulos = [s["title"] for s in groups[0]["sections"]]
    assert titulos == ["UNIDAD 1: FASTAPI", "UNIDAD 1: FASTAPI"]


def test_entrada_vacia_devuelve_vacio():
    assert group_candidates([]) == []
