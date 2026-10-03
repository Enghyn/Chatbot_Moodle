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
