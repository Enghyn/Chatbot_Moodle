"""Pipeline scrape: secciones via indice -> actividades -> detalle con fecha."""

from datetime import datetime

from bot_moodle.scrape import collect_candidates

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
