"""7.1 + unit-section-headers: agrupacion Curso > `Unidad - Apartado`, omite vacios."""

from bot_moodle.grouping import group_candidates


def _c(id_, course, section, apartado, idx=0, unidad_padre=None):
    from datetime import datetime

    return {
        "id": id_,
        "title": f"act {id_}",
        "due": datetime(2026, 10, 2, 23, 59),
        "course": course,
        "section": section,
        "apartado": apartado,
        "unidad_padre": unidad_padre,
        "section_index": idx,
    }


def test_apartado_sin_candidatas_no_muestra_encabezado():
    cands = [_c("1", "BD2", "Unidad 4", "Práctica 💻")]
    groups = group_candidates(cands)
    titulos = [g["title"] for g in groups[0]["groups"]]
    assert titulos == ["Práctica 💻"]  # sin padre: apartado solo, como antes
    assert "Actividades 🧩" not in titulos


def test_mismo_titulo_distinto_indice_sin_padre_colapsa_verbatim():
    # Sin unidad_padre la clave cae a (seccion, apartado): mismo titulo
    # verbatim comparte grupo en vez de repetirse por indice.
    cands = [
        _c("1", "Programación", "Práctica 💻", "Práctica 💻", idx=2),
        _c("2", "Programación", "Práctica 💻", "Práctica 💻", idx=8),
    ]
    groups = group_candidates(cands)
    titulos = [g["title"] for g in groups[0]["groups"]]
    assert titulos == ["Práctica 💻"]
    assert len(groups[0]["groups"][0]["items"]) == 2


def test_entrada_vacia_devuelve_vacio():
    assert group_candidates([]) == []
