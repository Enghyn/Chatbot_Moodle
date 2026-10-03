"""6.2: Ingles sin filtro de comision (todo entra)."""

from bot_moodle.comision import should_include


def test_ingles_con_marca_ajena_igual_entra():
    assert should_include("Quiz 2prog3 solo", "52527", course="Inglés") is True
    assert should_include("Quiz (Prof. Yácomo)", "52528", course="Inglés") is True
    assert should_include("Quiz Com1", "52529", course="Inglés") is True


def test_ingles_con_id_excluido_igual_entra():
    # ni la exclusion list aplica a Ingles: el bypass es total
    assert should_include("Subir trabajo de UML a Java", "1457", course="Inglés") is True


def test_bypass_acepta_variantes_de_nombre():
    assert should_include("Quiz 2prog3", "1", course="inglés") is True
    assert should_include("Quiz 2prog3", "1", course="INGLÉS") is True
