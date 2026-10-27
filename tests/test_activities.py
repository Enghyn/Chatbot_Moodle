"""3.2: extraccion de actividades desde vistas de seccion y paginas de detalle."""

from pathlib import Path

from bot_moodle.activities import extract_activities, extract_activity_from_detail

FIX = Path(__file__).parent / "fixtures"


def _html(name):
    return (FIX / name).read_text(encoding="utf-8")


def test_ingles_extrae_questionnaire_5():
    acts = extract_activities(_html("tema_ingles_class5.html"))
    por_id = {a["id"]: a for a in acts}
    assert "52527" in por_id
    assert "Questionnaire #5" in por_id["52527"]["title"]


def test_bd2_extrae_tp_u4_y_salta_yacomo_sin_link():
    acts = extract_activities(_html("tema_bd2_practica.html"))
    por_id = {a["id"]: a for a in acts}
    assert "56812" in por_id  # TP-U4
    assert "Unidad 4" in por_id["56812"]["title"]
    assert not any("como" in a["title"] for a in acts), "Yácomo (isrestricted sin link) debe saltarse"
    assert all(a["url"] for a in acts)
    assert len(acts) == 3  # 2 resources + 1 assign; sin link quedan fuera


def test_metodologia_extrae_entrega_u6():
    acts = extract_activities(_html("tema_metodologia_practica.html"))
    por_id = {a["id"]: a for a in acts}
    assert "1581" in por_id
    assert "Unidad 6" in por_id["1581"]["title"]


def test_prog3_extrae_fastapi():
    acts = extract_activities(_html("tema_prog3_practica.html"))
    por_id = {a["id"]: a for a in acts}
    assert "1384" in por_id
    assert "FastApi" in por_id["1384"]["title"]


def test_detalle_uml_devuelve_actividad_1457():
    act = extract_activity_from_detail(
        _html("assign_uml_1457.html"),
        url="https://campustest.frm.utn.edu.ar/mod/assign/view.php?id=1457",
    )
    assert act["id"] == "1457"
    assert "UML" in act["title"]


def test_wrapper_sin_link_se_descarta_aunque_tenga_nombre():
    acts = extract_activities(
        '<ul><li class="activity-wrapper modtype_assign">'
        '<div data-activityname="Solo etiqueta"></div>'
        "</li></ul>"
    )
    assert acts == []


# --- D1: identidad de la actividad (spec: "Identidad de la actividad por modulo de curso") ---


def test_seccion42_real_registra_el_cmid_y_no_el_id_del_curso():
    """Fixture real de la sección 42 del curso 14: el cmid sale del DOM."""
    acts = extract_activities(_html("prog3_seccion42_relaciones.html"))
    assert [a["id"] for a in acts] == ["1833"]
    assert all(a["id"] != "14" for a in acts), "nunca el id del curso (14)"
    assert acts[0]["modtype"] == "assign"
    assert "Libreria" in acts[0]["title"]


def test_ancla_course_view_resuelve_por_el_fragmento_module_y_no_por_el_id_del_curso():
    """El unico anchor con `id=` es del curso: no puede Gainar id=14."""
    acts = extract_activities(
        '<ul><li class="activity activity-wrapper assign modtype_assign hasinfo"'
        ' data-for="cmitem">'
        '<div data-activityname="Entrega"></div>'
        '<a href="https://cv/course/view.php?id=14&section=40#module-1522">ir</a>'
        "</li></ul>"
    )
    assert [a["id"] for a in acts] == ["1522"], "debe resolverse por la fuente 3 (#module-N)"


def test_sin_fuente_de_id_la_actividad_se_descarta():
    """Sin data-id, sin id=module-N, sin mod/*/view.php y sin #module-N -> fuera."""
    acts = extract_activities(
        '<ul><li class="activity-wrapper resource modtype_resource">'
        '<div data-activityname="Página huérfana"></div>'
        '<a href="https://cv/course/view.php?id=14&section=40">ir</a>'
        "</li></ul>"
    )
    assert acts == []


def test_data_id_gana_sobre_un_ancla_con_id_de_curso_dentro_del_mismo_li():
    """La fuente autoritativa (data-id) manda sobre cualquier link del contenedor."""
    acts = extract_activities(
        '<ul><li class="activity-wrapper assign modtype_assign" id="module-1833" data-id="1833">'
        '<span class="instancename">Entrega TP Libreria Backend</span>'
        '<a href="https://cv/course/view.php?id=14&section=40#module-1833">ir</a>'
        "</li></ul>"
    )
    assert [a["id"] for a in acts] == ["1833"]


def test_detalle_no_deriva_el_id_del_parametro_id_de_course_view():
    """2.5: `course/view.php?id=14` es el curso, no la actividad."""
    act = extract_activity_from_detail(
        "<html><body><ol class='breadcrumb'><li>PROG3A26</li><li>Relaciones</li>"
        "<li>Entrega</li></ol></body></html>",
        url="https://cv/course/view.php?id=14&section=40#module-1522",
    )
    assert act["id"] == "1522"
    assert act["id"] != "14"


def test_detalle_sin_fragmento_de_modulo_deja_el_id_vacio_y_no_el_del_curso():
    act = extract_activity_from_detail(
        "<html><body><ol class='breadcrumb'><li>C</li><li>S</li><li>A</li></ol></body></html>",
        url="https://cv/course/view.php?id=14&section=40",
    )
    assert act["id"] == ""
    assert act["id"] != "14"


def test_detalle_Real_libreria_1833_conserva_id_y_titulo_verbatim():
    act = extract_activity_from_detail(
        _html("assign_libreria_1833.html"),
        url="https://campustest.frm.utn.edu.ar/mod/assign/view.php?id=1833",
    )
    assert act["id"] == "1833"
    assert "Libreria" in act["title"]
    assert act["modtype"] == "assign"


def test_detalle_toma_el_cmid_del_body_del_dom_aunque_la_url_sea_del_curso():
    """El HTML real trae `cmid-1833` en el body: fuente autoritativa del detalle."""
    act = extract_activity_from_detail(
        _html("assign_libreria_1833.html"),
        url="https://campustest.frm.utn.edu.ar/course/view.php?id=14&section=40",
    )
    assert act["id"] == "1833"
    assert act["id"] != "14"
