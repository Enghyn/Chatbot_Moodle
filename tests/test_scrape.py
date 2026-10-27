"""Pipeline scrape: secciones via indice -> actividades -> detalle con fecha."""

import logging
from datetime import datetime
from pathlib import Path

from bot_moodle.scrape import collect_candidates

FIX = Path(__file__).parent / "fixtures"

SECTION_HTML = """
<html><body>
<select>
<option value="/course/view.php?id=14&section=0">HTML</option>
<option value="/course/view.php?id=14&section=2">Práctica 💻</option>
</select>
<ul><li class="activity-wrapper modtype_assign">
<div data-activityname="Entrega FastApi"></div>
<span class="instancename">Entrega FastApi Tarea</span>
<a href="https://cv/mod/assign/view.php?id=1384">ir</a>
</li></ul>
</body></html>
"""

DETAIL_CON_FECHA = """
<html><body>
<ol class="breadcrumb"><li>PROG3A26</li><li>Práctica 💻</li><li>Entrega FastApi</li></ol>
<div data-region="activity-dates">
<div><strong>Apertura:</strong> lunes, 5 de octubre de 2026, 08:00</div>
<div><strong>Cierre:</strong> viernes, 9 de octubre de 2026, 23:59</div>
</div>
</body></html>
"""


class _Resp:
    def __init__(self, text):
        self.text = text


class _FakeSession:
    def get(self, url, timeout=20):
        if "assign" in url:
            return _Resp(DETAIL_CON_FECHA)
        return _Resp(SECTION_HTML)


def test_collect_recorre_secciones_y_parsea_fecha():
    cands = collect_candidates(
        sessions={"C2": _FakeSession()},
        targets=[{"campus": "C2", "course_id": "14", "course": "Programación",
                  "base_url": "https://cv",
                  "sections": [{"index": 0, "title": "HTML"}, {"index": 2, "title": "Práctica 💻"}]}],
    )
    assert len(cands) == 2  # 1 actividad x 2 secciones recorridas
    assert all(c["due"] == datetime(2026, 10, 9, 23, 59) for c in cands)
    assert [c["section"] for c in cands] == ["HTML", "Práctica 💻"]  # verbatim del indice
    assert all(c["apartado"] == "Práctica 💻" for c in cands)  # verbatim del breadcrumb


def test_collect_descarta_sin_fecha_en_silencio():
    class _SinFecha(_FakeSession):
        def get(self, url, timeout=20):
            return _Resp("<html><body><ol class='breadcrumb'><li>C</li><li>S</li><li>A</li></ol></body></html>")

    cands = collect_candidates(
        sessions={"C2": _SinFecha()},
        targets=[{"campus": "C2", "course_id": "14", "course": "Programación",
                  "base_url": "https://cv", "sections": [0]}],
    )
    assert cands == []


# --- D2: el descarte deja rastro (spec: "Solo entregas con fecha parseable") ---


def _fix(name):
    return (FIX / name).read_text(encoding="utf-8")


class _FixturesSession:
    """Sirve HTML real: la vista de sección y el detalle tal cual lo bajamos."""

    def __init__(self, section, detail):
        self._section, self._detail = section, detail

    def get(self, url, timeout=20):
        return _Resp(self._detail if "mod/" in url else self._section)


def _warnings(caplog):
    return [r for r in caplog.records if r.levelname == "WARNING"]


def _target(**kw):
    base = {"campus": "C2", "course_id": "14", "course": "Programación",
            "base_url": "https://cv", "sections": [{"index": 40, "title": "Práctica 💻"}]}
    base.update(kw)
    return [base]


def test_descarte_por_sin_fecha_emite_warning_con_id_titulo_curso_y_seccion(caplog):
    """Vista real de BD2 + detalle real del cm 56812 (sin activity-dates)."""
    with caplog.at_level(logging.WARNING):
        cands = collect_candidates(
            sessions={"C2": _FixturesSession(
                _fix("tema_bd2_practica.html"), _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(course="BD2", course_id="723"),
        )
    assert cands == []
    warns = [r.getMessage() for r in _warnings(caplog)]
    assert warns, "el descarte por falta de fecha debe quedar registrado"
    sin_fecha = [m for m in warns if "sin_fecha" in m]
    assert len(sin_fecha) == 3, f"3 actividades BD2 sin fecha: {sin_fecha}"
    detalle = [m for m in sin_fecha if "56812" in m][0]
    assert "Trabajo Pr" in detalle and "Unidad 4" in detalle   # título verbatim
    assert "assign" in detalle                                  # modtype
    assert "723" in detalle                                     # curso
    assert "40" in detalle and "Práctica" in detalle            # sección (index + título)


def test_descarte_por_sin_id_emite_su_propio_motivo(caplog):
    """Del HTML real de BD2 quedan 2 wrappers sin identidad y ambos se reportan.

    Son los dos que antes se saltaban en silencio: la etiqueta `label` 56723
    (no tiene pagina propia) y el assign 56983 de la Comision Prof. Yacomo
    (`isrestricted` sin link)."""
    with caplog.at_level(logging.WARNING):
        collect_candidates(
            sessions={"C2": _FixturesSession(
                _fix("tema_bd2_practica.html"), _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(course="BD2", course_id="723"),
        )
    sin_id = [r.getMessage() for r in _warnings(caplog) if "sin_id" in r.getMessage()]
    assert len(sin_id) == 2, f"etiqueta + assign isrestricted: {sin_id}"
    etiqueta = [m for m in sin_id if "FNBC" in m][0]
    assert "56723" not in etiqueta and "modtype=label" in etiqueta
    yacomo = [m for m in sin_id if "Yácomo" in m][0]
    assert "modtype=assign" in yacomo
    assert "723" in yacomo and "40" in yacomo   # curso y sección también


def test_los_motivos_de_descarte_son_distinguibles(caplog):
    """Cada motivo aparece con su propio texto: sin_id no se confunde con sin_fecha."""
    with caplog.at_level(logging.WARNING):
        collect_candidates(
            sessions={"C2": _FixturesSession(
                _fix("tema_bd2_practica.html"), _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(course="BD2", course_id="723"),
        )
    motivos = {r.getMessage().split("motivo=")[1].split()[0] for r in _warnings(caplog)}
    assert motivos == {"sin_id", "sin_fecha"}


def _seccion_60_sin_fecha(n=60):
    """Vista de seccion sintetica: n activities con identidad pero sin fecha.

    El detalle servido (`assign_bd2_tp_u4_56812.html`) no trae activity-dates,
    asi que las n actividades se descartan con motivo `sin_fecha`."""
    wrappers = "".join(
        f'<li class="activity-wrapper assign modtype_assign" id="module-{9000+i}" data-id="{9000+i}">'
        f'<div data-activityname="Entrega {i}"></div>'
        f'<a href="https://cv/mod/assign/view.php?id={9000+i}">ir</a></li>'
        for i in range(n)
    )
    return f"<html><body><ul>{wrappers}</ul></body></html>"


def test_mas_de_50_descartes_cortan_el_detalle_en_50_y_el_cierre_refleja_el_total_real(caplog):
    """El techo de ruido (D2) corta el detalle por item; el total real vive en el cierre (D3)."""
    n = 60
    with caplog.at_level(logging.INFO):
        cands = collect_candidates(
            sessions={"C2": _FixturesSession(_seccion_60_sin_fecha(n),
                                             _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(),
        )
    assert cands == []
    warns = [r.getMessage() for r in _warnings(caplog)]
    detalle = [m for m in warns if "motivo=sin_fecha" in m]
    assert len(detalle) == 50, f"el detalle se corta en el umbral (50), no {len(detalle)}"
    cierres = [r.getMessage() for r in caplog.records
               if r.levelname == "INFO" and "corrida:" in r.getMessage()]
    assert len(cierres) == 1, f"un unico cierre por corrida: {cierres}"
    assert "descartes_por_motivo={'sin_fecha': 60}" in cierres[0], \
        f"el cierre debe reflejar el total real ({n}), no el techo: {cierres[0]}"


def test_el_warning_de_descarte_no_expone_secretos(caplog):
    """Regla dura 1 / RN-GLB-02: ni cookies, ni token, ni usuario, ni password."""
    cookies = "MoodleSession=abc123; logintoken=zzz999; usuario=enzo; password=secreto"
    section = (
        '<html><body><ul>'
        '<li class="activity-wrapper assign modtype_assign" id="module-7001" data-id="7001">'
        f'<div data-activityname="Entrega 7001"></div>'
        f'<a href="https://cv/mod/assign/view.php?id=7001&sesskey={cookies}">ir</a></li>'
        "</ul></body></html>"
    )
    with caplog.at_level(logging.WARNING):
        collect_candidates(
            sessions={"C2": _FixturesSession(section, _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(),
        )
    warns = [r.getMessage() for r in _warnings(caplog)]
    assert warns, "debe haber al menos un descarte registrado"
    joined = " ".join(warns).lower()
    for prohibido in ("moodlesession", "logintoken", "sesskey", "password", "contraseña",
                      "usuario", "cookie", "token"):
        assert prohibido not in joined, f"fuga de secreto en el log: {prohibido}"


# --- D3: resumen de cierre de corrida ---


def test_cierre_de_corrida_emite_info_con_secciones_actividades_candidatas_descartes_y_duracion(caplog):
    with caplog.at_level(logging.INFO):
        collect_candidates(
            sessions={"C2": _FixturesSession(
                _fix("tema_bd2_practica.html"), _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(course="BD2", course_id="723"),
        )
    infos = [r.getMessage() for r in caplog.records if r.levelname == "INFO"]
    resumen = [m for m in infos if "corrida:" in m]
    assert len(resumen) == 1, f"un único resumen por corrida: {infos}"
    m = resumen[0]
    assert "secciones=1" in m
    assert "actividades=3" in m          # 2 resources + 1 assign con identidad
    assert "candidatas=0" in m
    assert "descartes_por_motivo={'sin_fecha': 3, 'sin_id': 2}" in m
    assert "duracion_s=" in m


def test_duracion_es_un_numero_real_y_no_un_placeholder(caplog):
    with caplog.at_level(logging.INFO):
        collect_candidates(
            sessions={"C2": _FixturesSession(
                _fix("tema_bd2_practica.html"), _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(course="BD2", course_id="723"),
        )
    m = [r.getMessage() for r in caplog.records if "corrida:" in r.getMessage()][0]
    dur = float(m.split("duracion_s=")[1])
    assert dur >= 0.0


def test_el_resumen_no_expone_secretos(caplog):
    """El resumen de cierre va al mismo log: tampoco filtra secretos."""
    with caplog.at_level(logging.INFO):
        collect_candidates(
            sessions={"C2": _FixturesSession(
                _fix("tema_bd2_practica.html"), _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(course="BD2", course_id="723"),
        )
    m = [r.getMessage() for r in caplog.records if "corrida:" in r.getMessage()][0]
    for prohibido in ("moodlesession", "logintoken", "sesskey", "password", "cookie"):
        assert prohibido not in m.lower()


def test_una_corrida_con_candidatas_no_emite_warning_de_resumen_agregado(caplog):
    """Bajo el umbral, el resumen es INFO limpio: no se inunda el log."""
    with caplog.at_level(logging.INFO):
        cands = collect_candidates(
            sessions={"C2": _FakeSession()},
            targets=[{"campus": "C2", "course_id": "14", "course": "Programación",
                      "base_url": "https://cv",
                      "sections": [{"index": 2, "title": "Práctica 💻"}]}],
        )
    assert len(cands) == 1
    assert [r.getMessage() for r in _warnings(caplog)] == []
    m = [r.getMessage() for r in caplog.records if "corrida:" in r.getMessage()][0]
    assert "candidatas=1" in m and "descartes_por_motivo={}" in m


def test_sobre_el_umbral_el_cierre_es_info_totalmente_interpolado_con_el_truncamiento(caplog):
    """Regresion de produccion 2026-10-27: el cierre sobre-umbral salia como WARNING
    con el format string crudo y la tupla de args en repr."""
    with caplog.at_level(logging.INFO):
        cands = collect_candidates(
            sessions={"C2": _FixturesSession(_seccion_60_sin_fecha(60),
                                             _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(),
        )
    assert cands == []
    cierres = [r for r in caplog.records if "corrida:" in r.getMessage()]
    assert len(cierres) == 1, f"un unico cierre por corrida: {[r.getMessage() for r in cierres]}"
    rec = cierres[0]
    assert rec.levelname == "INFO", f"el cierre es informacion operativa, no anomalia: {rec.levelname}"
    m = rec.getMessage()
    for placeholder in ("%d", "%s", "%.1f"):
        assert placeholder not in m, f"placeholder sin interpolar en el cierre: {m}"
    assert "secciones=1" in m, f"secciones sin interpolar: {m}"
    assert "actividades=60" in m, f"actividades sin interpolar: {m}"
    assert "candidatas=0" in m, f"candidatas sin interpolar: {m}"
    assert "descartes_por_motivo={'sin_fecha': 60}" in m, f"resumen de motivos alterado: {m}"
    assert "descartes_detalle_omitido=" in m, f"falta el campo de truncamiento: {m}"
    assert "descartes_detalle_omitido=10" in m, f"60 descartes - umbral 50 = 10 omitidos: {m}"


def test_sobre_el_umbral_la_duracion_del_cierre_es_parseable_como_float(caplog):
    """Este es el test que habria fallado con el log real de produccion."""
    with caplog.at_level(logging.INFO):
        collect_candidates(
            sessions={"C2": _FixturesSession(_seccion_60_sin_fecha(60),
                                             _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(),
        )
    m = [r.getMessage() for r in caplog.records if "corrida:" in r.getMessage()][0]
    dur = float(m.split("duracion_s=")[1].split()[0])
    assert dur >= 0.0, f"duracion no parseable o negativa: {dur}"


def test_sobre_el_umbral_no_se_emite_el_warning_de_resumen_agregado(caplog):
    """El techo de ruido de D2 ya no duplica el cierre con un WARNING aparte."""
    with caplog.at_level(logging.WARNING):
        collect_candidates(
            sessions={"C2": _FixturesSession(_seccion_60_sin_fecha(60),
                                             _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(),
        )
    warns = [r.getMessage() for r in _warnings(caplog)]
    agregados = [m for m in warns if "resumen agregado" in m]
    assert agregados == [], f"el resumen agregado ya no es un WARNING separado: {agregados}"
    detalle = [m for m in warns if "motivo=sin_fecha" in m]
    assert len(detalle) == 50, f"el detalle por item sigue cortandose en 50: {len(detalle)}"


def test_bajo_el_umbral_el_cierre_no_lleva_el_campo_de_truncamiento(caplog):
    """Sin truncamiento no se inventa el campo: BD2 deja 5 descartes, muy por debajo."""
    with caplog.at_level(logging.INFO):
        collect_candidates(
            sessions={"C2": _FixturesSession(
                _fix("tema_bd2_practica.html"), _fix("assign_bd2_tp_u4_56812.html"))},
            targets=_target(course="BD2", course_id="723"),
        )
    m = [r.getMessage() for r in caplog.records if "corrida:" in r.getMessage()][0]
    assert "descartes_por_motivo={'sin_fecha': 3, 'sin_id': 2}" in m
    assert "descartes_detalle_omitido" not in m, f"bajo el umbral no hay nada omitido: {m}"

