"""Alias de profesores de comision 4 (cierra 3.1 del go-live)."""

from bot_moodle.comision import should_include


def test_profesor_bd_propio_incluye():
    assert should_include("TP Unidad 4 (Comisión Prof. Sergio Neira)", "90001", "BD2") is True


def test_profesores_ingles_propios_incluyen():
    assert should_include("M2 Quiz (Prof. Buccella - Farías)", "90002", "Inglés") is True


def test_profesor_prog_propio_incluye():
    assert should_include("Entrega Clase 5 (Prof. Espejo)", "90003", "Programación") is True
    assert should_include("TP Integrador (Prof. Matias Torres)", "90004", "Programación") is True


def test_profesor_ajeno_sigue_excluido():
    assert should_include("TP Unidad 4 (Comisión Prof. Yácomo)", "90005", "BD2") is False


def test_apellido_comun_sin_prof_no_cambia_default():
    # "espejo"/"torres" sueltos no fuerzan nada: default inclusivo ya los incluye
    assert should_include("Ejercicio espejo de prueba", "90006", "Programación") is True


def test_profesor_desconocido_en_contexto_comision_excluye():
    assert should_include("TP Unidad 4 (Comisión Prof. García)", "90007", "BD2") is False


def test_mencion_prof_sin_contexto_comision_no_excluye():
    assert should_include("Reunión con el prof. de consulta", "90008", "BD2") is True
