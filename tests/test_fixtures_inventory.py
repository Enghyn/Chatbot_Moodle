"""1.3: las evidencias HTML viven como fixtures documentadas.

Desde `visibilidad-y-diagnostico-actividades` hay 10: se incorporan la vista de
la sección 42 del curso 14 y el detalle del cm 1833 (D5: los nombres nuevos
llevan el número de sección porque el curso 14 tiene tres tabs "Práctica 💻").
"""

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"
MANIFEST = FIXTURES / "manifest.json"

EXPECTED = {
    "tema_ingles_class5.html": {"curso": "Inglés", "seccion": "Class 5", "tiene_fecha": True},
    "tema_bd2_practica.html": {"curso": "BD2", "seccion": "Práctica", "tiene_fecha": False},
    "tema_metodologia_practica.html": {"curso": "Metodología", "seccion": "Práctica", "tiene_fecha": False},
    "tema_prog3_practica.html": {"curso": "Programación", "seccion": "Práctica", "tiene_fecha": False},
    "assign_bd2_tp_u4_56812.html": {"curso": "BD2", "seccion": "Práctica", "tiene_fecha": False},
    "assign_met_u6_1581.html": {"curso": "Metodología", "seccion": "Práctica", "tiene_fecha": False},
    "assign_fastapi_1384.html": {"curso": "Programación", "seccion": "Práctica", "tiene_fecha": False},
    "assign_uml_1457.html": {"curso": "Programación", "seccion": "Actividades", "tiene_fecha": True},
    "prog3_seccion42_relaciones.html": {
        "curso": "Programación",
        "seccion": "Práctica 💻 (sección 42)",
        "tiene_fecha": False,
    },
    "assign_libreria_1833.html": {
        "curso": "Programación",
        "seccion": "Práctica 💻 (sección 42)",
        "tiene_fecha": True,
    },
}


def test_las_10_fixtures_existen():
    faltantes = [n for n in EXPECTED if not (FIXTURES / n).exists()]
    assert faltantes == [], f"fixtures faltantes: {faltantes}"


def test_manifest_documenta_curso_seccion_y_fecha():
    assert MANIFEST.exists(), "falta tests/fixtures/manifest.json"
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert set(data.keys()) == set(EXPECTED.keys())
    for nombre, esperado in EXPECTED.items():
        entry = data[nombre]
        assert entry["curso"] == esperado["curso"], nombre
        assert entry["seccion"] == esperado["seccion"], nombre
        assert entry["tiene_fecha"] is esperado["tiene_fecha"], nombre
        assert entry["origen"], f"{nombre} sin archivo origen documentado"


def test_fixtures_nuevos_de_la_seccion_42_declaran_su_numero_de_seccion():
    """D5: sin el numero de seccion, guardar por titulo de tab pisa archivos."""
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert data["prog3_seccion42_relaciones.html"]["seccion_numero"] == 42
    assert data["assign_libreria_1833.html"]["seccion_numero"] == 42
    assert "42" in "prog3_seccion42_relaciones.html"
    assert "seccion42" in "prog3_seccion42_relaciones.html"
