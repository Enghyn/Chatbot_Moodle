"""2.x: login Moodle por campus + reporte de fallo sin abortar el otro."""

from bot_moodle.session import (
    CampusResult,
    extract_login_token,
    login_campus,
)


class _FakeResp:
    def __init__(self, text="", status=200):
        self.text = text
        self.status_code = status


class _FakeSession:
    """Doble de requests.Session: GET devuelve login con token, POST valida."""

    def __init__(self, valid_user="alumno", valid_pass="clave", token="TOK123"):
        self.valid = (valid_user, valid_pass)
        self.token = token
        self.posted = []

    def get(self, url, timeout=20):
        return _FakeResp(
            f'<html><body><form><input type="hidden" name="logintoken" value="{self.token}"></form></body></html>'
        )

    def post(self, url, data=None, timeout=20):
        self.posted.append(data)
        if (data.get("username"), data.get("password")) == self.valid and data.get("logintoken") == self.token:
            return _FakeResp("<html>Panel principal</html>")
        return _FakeResp("<html>Invalid login, please try again</html>")


def _campus(user="alumno", password="clave", base="https://campus.example", name="C1"):
    from bot_moodle.config import CampusConfig

    return CampusConfig(name=name, base_url=base, username=user, password=password)


def test_extrae_logintoken_del_formulario():
    html = '<form><input name="username"><input type="hidden" name="logintoken" value="ABC99"></form>'
    assert extract_login_token(html) == "ABC99"


def test_extrae_logintoken_con_comillas_simples_y_orden_inverso():
    html = "<input value='XYZ' type='hidden' name='logintoken'>"
    assert extract_login_token(html) == "XYZ"


def test_login_valido_devuelve_sesion_ok():
    result = login_campus(_campus(), session=_FakeSession())
    assert isinstance(result, CampusResult)
    assert result.ok is True
    assert result.session is not None


def test_login_invalido_reporta_fallo_con_motivo():
    result = login_campus(_campus(password="mal"), session=_FakeSession())
    assert result.ok is False
    assert result.session is None
    assert "login" in result.error.lower() or "invalid" in result.error.lower()


def test_un_campus_fallido_no_aborta_el_otro():
    from bot_moodle.session import login_all

    bueno = _campus(user="alumno", password="clave", name="C1")
    malo = _campus(user="nadie", password="mal", name="C2")
    results = login_all(
        [bueno, malo],
        session_factory=lambda c: _FakeSession(),
    )
    assert results[bueno.name].ok is True
    assert results[malo.name].ok is False
    # el ciclo continúa: ambos campus tienen resultado registrado
    assert set(results.keys()) == {bueno.name, malo.name}
