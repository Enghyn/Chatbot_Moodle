"""3.1: enumerar TODAS las secciones via indice (no solo la vista Tema actual)."""

from pathlib import Path

from bot_moodle.sections import enumerate_sections

FIX = Path(__file__).parent / "fixtures"


def _html(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_bd2_lista_todas_las_secciones_incluye_unidad_4():
    secs = enumerate_sections(_html("tema_bd2_practica.html"))
    titulos = [s["title"] for s in secs]
    assert len(secs) >= 20, f"solo {len(secs)} secciones"
    assert any("Unidad 4" in t for t in titulos)
    assert any(s.get("index") == 0 for s in secs)  # seccion 0 = general


def test_prog3_lista_mas_de_30_e_incluye_fastapi():
    secs = enumerate_sections(_html("tema_prog3_practica.html"))
    titulos = [s["title"] for s in secs]
    assert len(secs) >= 30, f"solo {len(secs)} secciones"
    assert any("FastAPI" in t or "FastApi" in t for t in titulos)


def test_ingles_sin_options_usa_fallback_y_no_toma_mensajeria():
    secs = enumerate_sections(_html("tema_ingles_class5.html"))
    titulos = [s["title"] for s in secs]
    assert len(secs) >= 5, f"solo {len(secs)} secciones"
    assert any("Class 5" in t for t in titulos)
    assert not any("mensajer" in t.lower() or "conversacion" in t.lower() for t in titulos)


def test_metodologia_lista_todas_las_unidades():
    secs = enumerate_sections(_html("tema_metodologia_practica.html"))
    titulos = [s["title"] for s in secs]
    assert len(secs) >= 30, f"solo {len(secs)} secciones"
    assert any("Unidad 6" in t for t in titulos)
