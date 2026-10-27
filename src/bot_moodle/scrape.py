"""Scrape: curso -> secciones (indice) -> actividades -> detalle (fecha+breadcrumb)."""

from __future__ import annotations

import logging
import time
from collections import Counter
from typing import Any

from bot_moodle.activities import extract_activities
from bot_moodle.breadcrumbs import parse_breadcrumb
from bot_moodle.dates import parse_activity_dates
from bot_moodle.sections import resolve_parent_unit

logger = logging.getLogger(__name__)

#: Techo de ruido (D2): pasado este numero de descartes en una corrida, el detalle
#: uno por uno se sustituye por el resumen agregado del cierre. Hoy hay al menos 3
#: assigns conocidos sin fecha que inundarian el log.
DESCARTES_UMBRAL = 50


class _RegistroDescartes:
    """Acumula descartes de una corrida y los deja registrables (D2).

    Emite un `warning` por actividad hasta `DESCARTES_UMBRAL`; de ahi en mas solo
    cuenta, y el cierre emite el resumen agregado. Nunca loguea cookies,
    `MoodleSession`, `logintoken`, `sesskey`, usuario ni password: solo el mismo
    conjunto de datos que ya viaja en el mensaje (id, titulo, modtype, curso,
    seccion, motivo).
    """

    def __init__(self, umbral: int = DESCARTES_UMBRAL) -> None:
        self.umbral = umbral
        self.conteo: Counter[str] = Counter()

    @property
    def total(self) -> int:
        return sum(self.conteo.values())

    def registrar(self, motivo: str, *, act: dict | None = None,
                  course_id: Any = "", section_index: Any = "", section_title: str = "") -> None:
        self.conteo[motivo] += 1
        if self.total > self.umbral:
            return  # ya estamos en modo resumen: no mas detalle uno por uno
        act = act or {}
        logger.warning(
            "descarte motivo=%s id=%s titulo=%r modtype=%s curso=%s seccion=%s (%s)",
            motivo,
            act.get("id") or "-",
            act.get("title") or "",
            act.get("modtype") or "-",
            course_id,
            section_index,
            section_title or "-",
        )

    def resumen_texto(self) -> str:
        return str(dict(sorted(self.conteo.items()))) if self.conteo else "{}"


def section_url(base_url: str, course_id: str, index: int) -> str:
    return f"{base_url.rstrip('/')}/course/view.php?id={course_id}&section={index}"


def collect_candidates(sessions: dict[str, Any], targets: list[dict], timeout: int = 20) -> list[dict]:
    """Recorre las secciones indicadas de cada curso y devuelve candidatas con fecha.

    targets: [{campus, course_id, course, base_url, sections: [{index, title}]}].
    La seccion verbatim viene del indice recorrido; el apartado, del breadcrumb
    del detalle. Las actividades sin fecha se descartan, pero **todo descarte
    queda registrado** con su motivo (D2), nunca silencioso.

    El costo de la corrida (~93 s medidos en produccion para 3 cursos x ~44
    secciones) queda observable con el resumen de cierre (D3): sin el, ni un
    descarte ni un alza de duracion son detectables en el log de EasyPanel.
    `unidad_padre` se deriva de `units` (tabs de unidad del curso, opcional):
    sin units -> None y la agrupacion usa el comportamiento anterior.
    """
    candidates: list[dict] = []
    descartes = _RegistroDescartes()
    n_secciones = 0
    n_actividades = 0
    inicio = time.monotonic()

    for t in targets:
        sess = sessions.get(t["campus"])
        if sess is None:
            descartes.registrar("sin_sesion", course_id=t.get("course_id"))
            logger.warning("%s: sin sesion, se omite curso %s", t["campus"], t.get("course_id"))
            continue
        units = t.get("units", []) or []
        for sec in t.get("sections", []):
            idx = sec["index"] if isinstance(sec, dict) else sec
            sec_title = sec["title"] if isinstance(sec, dict) else t.get("section_fallback", "")
            try:
                resp = sess.get(section_url(t["base_url"], t["course_id"], idx), timeout=timeout)
            except Exception as exc:
                descartes.registrar("seccion_fallo", course_id=t.get("course_id"),
                                    section_index=idx, section_title=sec_title)
                logger.warning("seccion %s/%s fallo: %s", t["course_id"], idx, exc)
                continue
            n_secciones += 1

            def _sin_id(act: dict, motivo: str, _idx=idx, _cid=t.get("course_id"),
                        _sec=sec_title) -> None:
                descartes.registrar(motivo, act=act, course_id=_cid,
                                    section_index=_idx, section_title=_sec)

            acts = extract_activities(resp.text or "", on_discard=_sin_id)
            n_actividades += len(acts)
            for act in acts:
                try:
                    detail = sess.get(act["url"], timeout=timeout)
                except Exception as exc:
                    descartes.registrar("detalle_fallo", act=act, course_id=t.get("course_id"),
                                        section_index=idx, section_title=sec_title)
                    logger.warning("detalle %s fallo: %s", act["id"], exc)
                    continue
                parsed = parse_activity_dates(detail.text or "")
                if parsed["due"] is None:
                    descartes.registrar("sin_fecha", act=act, course_id=t.get("course_id"),
                                        section_index=idx, section_title=sec_title)
                    continue  # sin fecha: default NO-notificar (RN-EXT-02), pero registrado
                crumb = parse_breadcrumb(detail.text or "")
                candidates.append(
                    {
                        "id": act["id"],
                        "title": act["title"],
                        "due": parsed["due"],
                        "start": parsed["start"],
                        "course": t.get("course", ""),
                        "section": sec_title,
                        "apartado": crumb["section"],
                        "unidad_padre": resolve_parent_unit(units, idx),
                        "section_index": idx,
                        "url": act["url"],
                    }
                )

    _resumen_cierre(
        secciones=n_secciones,
        actividades=n_actividades,
        candidatas=len(candidates),
        descartes=descartes,
        duracion_s=time.monotonic() - inicio,
    )
    return candidates


def _resumen_cierre(*, secciones: int, actividades: int, candidatas: int,
                    descartes: _RegistroDescartes, duracion_s: float) -> None:
    """D3: un unico resumen de cierre por corrida, siempre en INFO.

    Se interpola con f-string (no con argumentos diferidos) para que no exista
    forma de volver a imprimir un format string crudo. El techo de ruido de D2
    viaja como campo `descartes_detalle_omitido`, no como logger.warning aparte:
    el cierre es informacion operativa, y el WARNING queda reservado a los
    descartes individuales.
    """
    omitido = max(0, descartes.total - descartes.umbral)
    linea = (
        f"corrida: secciones={secciones} actividades={actividades} "
        f"candidatas={candidatas} descartes_por_motivo={descartes.resumen_texto()} "
        f"duracion_s={duracion_s:.1f}"
    )
    if omitido:
        linea += f" descartes_detalle_omitido={omitido}"
    logger.info(linea)


def _course_html(session: Any, base_url: str, course_id: str, timeout: int = 20) -> str:
    resp = session.get(section_url(base_url, course_id, 0), timeout=timeout)
    return resp.text or ""


def discover_sections(session: Any, base_url: str, course_id: str, timeout: int = 20) -> list[dict]:
    """Devuelve [{index, title, url}] con las secciones del curso via indice."""
    from bot_moodle.sections import enumerate_sections

    return [s for s in enumerate_sections(_course_html(session, base_url, course_id, timeout)) if s["index"] >= 0]


def discover_units(session: Any, base_url: str, course_id: str, timeout: int = 20) -> list[dict]:
    """Devuelve [{index, title}] con las tabs de unidad (padres de seccion)."""
    from bot_moodle.sections import extract_unit_tabs

    return extract_unit_tabs(_course_html(session, base_url, course_id, timeout))
