"""9.2: sender Evolution (POST /message/sendText, sin reintento en bucle)."""

from bot_moodle.sender import EvolutionSender, SendResult


class _Resp:
    def __init__(self, status=201, body="ok"):
        self.status_code = status
        self.text = body

    def json(self):
        return {"status": self.text}


class _SessionDown(Exception):
    pass


class _FakeHttp:
    """Doble de requests: cuenta POSTs para probar que no hay reintentos."""

    def __init__(self, resp=None, error=None):
        self.resp = resp or _Resp()
        self.error = error
        self.posts = []

    def post(self, url, headers=None, json=None, timeout=20):
        self.posts.append({"url": url, "json": json})
        if self.error is not None:
            raise self.error
        return self.resp


def _sender(http):
    return EvolutionSender(
        base_url="http://evo:8080",
        api_key="KEY",
        group_jid="123@g.us",
        instance="bot-moodle",
        http=http,
    )


def test_envio_exitoso_registra_un_post_con_jid_y_texto():
    http = _FakeHttp(_Resp(201, "sent"))
    result = _sender(http).send_text("hola *Comisión 4*")
    assert isinstance(result, SendResult)
    assert result.ok is True
    assert len(http.posts) == 1
    assert http.posts[0]["url"].endswith("/message/sendText/bot-moodle")
    assert http.posts[0]["json"]["number"] == "123@g.us"
    assert "Comisión 4" in http.posts[0]["json"]["text"]


def test_sesion_caida_reporta_y_no_reintenta_en_bucle():
    http = _FakeHttp(error=_SessionDown("closed"))
    result = _sender(http).send_text("hola")
    assert result.ok is False
    assert "sesi" in result.error.lower() or "closed" in result.error.lower()
    assert len(http.posts) == 1  # un solo intento, sin bucle


def test_respuesta_http_de_error_no_reintenta():
    http = _FakeHttp(_Resp(401, "unauthorized"))
    result = _sender(http).send_text("hola")
    assert result.ok is False
    assert len(http.posts) == 1
