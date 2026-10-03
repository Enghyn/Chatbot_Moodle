"""Login Moodle por campus: POST /login/index.php con logintoken + cookies.

Un campus fallido se reporta sin abortar el otro; los datos parciales
nunca se presentan como completos (ver CampusResult.ok / .error).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional

from bs4 import BeautifulSoup

from bot_moodle.config import CampusConfig

logger = logging.getLogger(__name__)

LOGIN_PATH = "/login/index.php"
_LOGIN_FAIL_MARKERS = ("invalid login", "error de acceso", "login incorrecto", "contrase")


def extract_login_token(login_html: str) -> str:
    """Extrae el logintoken del formulario de login (comillas/orden flexibles)."""
    soup = BeautifulSoup(login_html, "lxml")
    token = soup.find("input", attrs={"name": "logintoken"})
    if token is not None and token.get("value"):
        return str(token["value"])
    return ""


@dataclass
class CampusResult:
    name: str
    ok: bool
    session: Optional[Any] = None
    error: str = ""


def login_campus(campus: CampusConfig, session: Any = None, timeout: int = 20) -> CampusResult:
    """Hace login en un campus. Devuelve CampusResult (no lanza por fallo de login)."""
    import requests

    sess = session if session is not None else requests.Session()
    base = campus.base_url.rstrip("/")
    try:
        resp = sess.get(base + LOGIN_PATH, timeout=timeout)
        token = extract_login_token(resp.text or "")
        if not token:
            msg = f"{campus.name}: no se encontro logintoken en el formulario"
            logger.warning(msg)
            return CampusResult(name=campus.name, ok=False, error=msg)
        posted = sess.post(
            base + LOGIN_PATH,
            data={"username": campus.username, "password": campus.password, "logintoken": token},
            timeout=timeout,
        )
        body = (posted.text or "").lower()
        if any(m in body for m in _LOGIN_FAIL_MARKERS):
            msg = f"{campus.name}: login rechazado (credenciales invalidas)"
            logger.warning(msg)
            return CampusResult(name=campus.name, ok=False, error=msg)
        logger.info("%s: sesion valida", campus.name)
        return CampusResult(name=campus.name, ok=True, session=sess)
    except Exception as exc:  # red caida, timeout, DNS: reportar, no propagar
        msg = f"{campus.name}: fallo de conexion ({exc})"
        logger.warning(msg)
        return CampusResult(name=campus.name, ok=False, error=msg)


def login_all(
    campuses: list[CampusConfig],
    session_factory: Optional[Callable[[CampusConfig], Any]] = None,
    timeout: int = 20,
) -> dict[str, CampusResult]:
    """Loguea cada campus con su propia sesion; un fallo no aborta el resto."""
    import requests

    results: dict[str, CampusResult] = {}
    for campus in campuses:
        sess = session_factory(campus) if session_factory else requests.Session()
        results[campus.name] = login_campus(campus, session=sess, timeout=timeout)
    return results
