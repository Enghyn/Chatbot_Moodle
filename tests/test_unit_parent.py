"""unit-section-headers 1.1-1.3: tabs de unidad (nivel 0) y resolucion de `unidad_padre`.

Evidencia real (tests/fixtures/*.html, formato onetopic):
- Prog3: 9 tabs nivel-0 [HTML(0), CSS(6), JavaScript(11), TypeScript(15),
  POO(19), FastAPI(24), DevOps(29), SQLModel(35), Relaciones y Estado(40)]
  + 5 tabs nivel-1 hijas de FastAPI [Introduccion(24) ... Encuesta(28)].
- BD2: nivel-0 [General(0), U1(1), U2(6), U3(11), U4(16), Evaluaciones(41)]
  + nivel-1 hijas de U4 [Inicio(16), Actividades(17), Practica(18), Autoev(20)].
- Ingles: nivel-0 [Inicio(0), Module 1(2), Module 2(9), Midterm Test #1(13)]
  + nivel-1 hijas de Module 2 [Inicio(9), Class 4(10), Class 5(11), Class 6(12)].

Regla: padre(seccion) = tab de nivel-0 con mayor section <= seccion.
Sin tabs de nivel (formato sin niveles) -> fallback posicional por titulo
generico; sin candidato -> None (huerfana, formato anterior).
"""

from pathlib import Path

from bot_moodle.scrape import collect_candidates
from bot_moodle.sections import extract_unit_tabs, resolve_parent_unit

FIX = Path(__file__).parent / "fixtures"


def _html(name):
    return (FIX / name).read_text(encoding="utf-8")


# --- 1.1: extraccion ordenada de tabs de unidad (solo nivel 0) ---


def test_prog3_tabs_unidad_en_orden_con_css_antes_de_practica():
    units = extract_unit_tabs(_html("tema_prog3_practica.html"))
    titulos = [u["title"] for u in units]
    assert titulos == [
        "HTML", "CSS", "JavaScript", "TypeScript", "POO",
        "FastAPI", "DevOps", "SQLModel", "Relaciones y Estado",
    ]
    assert [u["index"] for u in units] == [0, 6, 11, 15, 19, 24, 29, 35, 40]
    # CSS (unidad) precede en nro de seccion a la Practica (sec 26, nivel 1)
    assert units[1] == {"index": 6, "title": "CSS"}
    assert not any("ctica" in t for t in titulos)  # nivel-1 excluido


def test_bd2_tabs_unidad_en_orden_con_unidad4_antes_de_practica():
    units = extract_unit_tabs(_html("tema_bd2_practica.html"))
    assert [(u["index"], u["title"]) for u in units] == [
        (0, "BASES DE DATOS 2 - General"),
        (1, "Unidad 1"), (6, "Unidad 2"), (11, "Unidad 3"),
        (16, "Unidad 4"), (41, "Evaluaciones"),
    ]


def test_ingles_tabs_unidad_excluye_clases_nivel1():
    units = extract_unit_tabs(_html("tema_ingles_class5.html"))
    assert [(u["index"], u["title"]) for u in units] == [
        (0, "Inicio"),
        (2, "Module 1: Interactions"),
        (9, "Module 2: Personal Presentations"),
        (13, "Midterm Test #1"),
    ]


def test_sin_tabs_de_nivel_devuelve_vacio():
    assert extract_unit_tabs("<html><body><p>sin navegacion</p></body></html>") == []


# --- 1.2: unidad_padre por seccion ---


def test_practica_prog3_sec26_padre_fastapi():
    # NOTA: tasks.md decia CSS, pero el fixture prueba que la Practica
    # sec 26 es hija de FastAPI (sec 24): "CSS - Practica" era solo ejemplo.
    units = extract_unit_tabs(_html("tema_prog3_practica.html"))
    assert resolve_parent_unit(units, 26) == "FastAPI"


def test_practica_bd2_sec18_padre_unidad4():
    units = extract_unit_tabs(_html("tema_bd2_practica.html"))
    assert resolve_parent_unit(units, 18) == "Unidad 4"
    # triangulacion: otra Practica de otra unidad no colapsa
    assert resolve_parent_unit(units, 8) == "Unidad 2"
    assert resolve_parent_unit(units, 3) == "Unidad 1"


def test_seccion_huerfana_sin_padre_es_none():
    assert resolve_parent_unit([], 18) is None
    units = extract_unit_tabs(_html("tema_bd2_practica.html"))
    assert resolve_parent_unit(units, -1) is None  # indice desconocido


def test_seccion_unidad_apunta_a_si_misma():
    units = extract_unit_tabs(_html("tema_bd2_practica.html"))
    assert resolve_parent_unit(units, 16) == "Unidad 4"  # Inicio(sec 16) -> U4
    assert resolve_parent_unit(units, 41) == "Evaluaciones"


# --- 1.3: jerarquia de Ingles Module > Class ---


def test_class5_padre_module2():
    units = extract_unit_tabs(_html("tema_ingles_class5.html"))
    assert resolve_parent_unit(units, 11) == "Module 2: Personal Presentations"
    # triangulacion: las Class son nivel-1, nunca padres entre si
    assert resolve_parent_unit(units, 10) == "Module 2: Personal Presentations"
    assert resolve_parent_unit(units, 2) == "Module 1: Interactions"


# --- 1.2b: propagacion en el dict de candidata (scrape) ---


class _Resp:
    def __init__(self, text):
        self.text = text


_DETAIL = """
<html><body>
<ol class="breadcrumb"><li>BD2</li><li>Práctica 💻</li><li>TP U4</li></ol>
<div data-region="activity-dates">
<div><strong>Cierre:</strong> viernes, 9 de octubre de 2026, 23:59</div>
</div>
</body></html>
"""


class _FakeSession:
    def __init__(self, section_html="<html></html>"):
        self.section_html = section_html

    def get(self, url, timeout=20):
        if "assign" in url:
            return _Resp(_DETAIL)
        return _Resp(self.section_html)


_SECTION_ACT = """
<html><body><ul><li class="activity-wrapper modtype_assign">
<div data-activityname="TP U4"></div>
<span class="instancename">TP U4 Tarea</span>
<a href="https://cv/mod/assign/view.php?id=1">ir</a>
</li></ul></body></html>
"""


def test_collect_propaga_unidad_padre_en_candidata():
    sess = _FakeSession(_SECTION_ACT)
    cands = collect_candidates(
        sessions={"C1": sess},
        targets=[{"campus": "C1", "course_id": "723", "course": "BD2",
                  "base_url": "https://cv",
                  "sections": [{"index": 18, "title": "Práctica 💻"}],
                  "units": [{"index": 16, "title": "Unidad 4"},
                            {"index": 41, "title": "Evaluaciones"}]}],
    )
    assert len(cands) == 1
    assert cands[0]["unidad_padre"] == "Unidad 4"
    # section/apartado intactos para filtros y debug
    assert cands[0]["section"] == "Práctica 💻"
    assert cands[0]["apartado"] == "Práctica 💻"


def test_collect_sin_units_padre_none_y_no_rompe():
    sess = _FakeSession(_SECTION_ACT)
    cands = collect_candidates(
        sessions={"C1": sess},
        targets=[{"campus": "C1", "course_id": "723", "course": "BD2",
                  "base_url": "https://cv",
                  "sections": [{"index": 18, "title": "Práctica 💻"}]}],
    )
    assert len(cands) == 1
    assert cands[0]["unidad_padre"] is None
