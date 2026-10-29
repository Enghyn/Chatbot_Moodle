"""8.1: estado persistente por assign id en estado.json."""

import json
import logging
from datetime import datetime
from pathlib import Path

import pytest

from bot_moodle.state import StateStore

NOW = datetime(2026, 9, 29, 8, 0)

ACCION = "accion=arranca_con_estado_vacio_puede_renotificar"


def _warns_state(caplog) -> list[str]:
    """Warnings emitidos por el módulo de estado, en orden de emisión."""
    return [
        r.getMessage()
        for r in caplog.records
        if r.levelname == "WARNING" and r.name == "bot_moodle.state"
    ]


def test_id_nuevo_se_registra_con_timestamp(tmp_path):
    store = StateStore(tmp_path / "estado.json")
    assert store.is_new("56812") is True
    store.mark_seen("56812", NOW)
    data = json.loads((tmp_path / "estado.json").read_text(encoding="utf-8"))
    assert "56812" in data
    assert data["56812"]["visto"]  # timestamp presente


def test_id_conocido_no_se_retrata_como_nuevo(tmp_path):
    store = StateStore(tmp_path / "estado.json")
    store.mark_seen("56812", NOW)
    store2 = StateStore(tmp_path / "estado.json")  # recarga desde disco
    assert store2.is_new("56812") is False
    assert store2.is_new("1384") is True


def test_flags_digest_y_urgente_por_id(tmp_path):
    store = StateStore(tmp_path / "estado.json")
    store.mark_seen("1", NOW)
    assert store.was_notified("1", "urgente") is False
    store.mark_notified("1", "urgente")
    assert store.was_notified("1", "urgente") is True
    assert store.was_notified("1", "digest") is False


# --- Carga diagnosticable (D1): ausente | vacio | corrupto | ok ---


def test_carga_ausente_es_warning_y_estado_ausente(tmp_path, caplog):
    """El caso de produccion: /data vacio tras un deploy -> estado ausente."""
    ruta = tmp_path / "estado.json"
    with caplog.at_level(logging.WARNING, logger="bot_moodle.state"):
        store = StateStore(ruta)
    assert store.estado == "ausente"
    assert store.is_new("1") is True  # se envia igual (fail-open)
    warns = _warns_state(caplog)
    assert len(warns) == 1, f"un unico warning por carga no sana: {warns}"
    assert "estado=ausente" in warns[0]
    assert f"ruta={ruta}" in warns[0]
    assert "motivo=archivo_inexistente" in warns[0]
    assert ACCION in warns[0]


@pytest.mark.parametrize(
    ("contenido", "motivo"),
    [("", "sin_contenido"), ("  \n\t  ", "sin_contenido"), ("{}", "objeto_sin_registros")],
    ids=["cero_bytes", "solo_espacios", "objeto_vacio"],
)
def test_carga_vacia_en_blanco_y_objeto_vacio(tmp_path, caplog, contenido, motivo):
    ruta = tmp_path / "estado.json"
    ruta.write_text(contenido, encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="bot_moodle.state"):
        store = StateStore(ruta)
    assert store.estado == "vacio"
    assert store.is_new("1") is True  # se envia igual
    warns = _warns_state(caplog)
    assert len(warns) == 1, f"un unico warning por carga no sana: {warns}"
    assert "estado=vacio" in warns[0]
    assert f"motivo={motivo}" in warns[0]


def test_carga_json_roto_es_corrupto_y_no_revienta(tmp_path, caplog):
    """Corte de escritura: el archivo truncado no puede matar la corrida."""
    ruta = tmp_path / "estado.json"
    ruta.write_text('{"1": {', encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="bot_moodle.state"):
        store = StateStore(ruta)
    assert store.estado == "corrupto"
    assert store.is_new("1") is True
    warns = _warns_state(caplog)
    assert len(warns) == 1, f"un unico warning por carga no sana: {warns}"
    assert "estado=corrupto" in warns[0]
    assert "motivo=json_invalido" in warns[0]
    # La corrida sigue y puede reescribir un estado sano desde cero.
    store.mark_seen("1", NOW)
    assert store.is_new("1") is False
    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert data["1"]["visto"] == NOW.isoformat()


@pytest.mark.parametrize(
    "contenido", ["null", "[]", '"texto"'], ids=["null", "lista", "texto"]
)
def test_carga_tipo_no_objeto_es_corrupto(tmp_path, caplog, contenido):
    """Bug extra: un JSON valido que no es dict reventaba is_new con TypeError."""
    ruta = tmp_path / "estado.json"
    ruta.write_text(contenido, encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="bot_moodle.state"):
        store = StateStore(ruta)
    assert store.estado == "corrupto"
    assert store.is_new("1") is True  # antes: TypeError, corrida muerta con codigo 1
    warns = _warns_state(caplog)
    assert len(warns) == 1, f"un unico warning por carga no sana: {warns}"
    assert "motivo=tipo_no_objeto" in warns[0]
    store.mark_seen("1", NOW)
    assert json.loads(ruta.read_text(encoding="utf-8"))["1"]["visto"] == NOW.isoformat()


def test_carga_sana_es_ok_sin_warning(tmp_path, caplog):
    ruta = tmp_path / "estado.json"
    ruta.write_text(json.dumps({"1": {"visto": NOW.isoformat()}}), encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="bot_moodle.state"):
        store = StateStore(ruta)
    assert store.estado == "ok"
    assert store.is_new("1") is False
    assert _warns_state(caplog) == []


def test_warning_de_estado_no_filtra_contenido_ni_secretos(tmp_path, caplog):
    """Regla dura 1: ruta + motivo, nunca el contenido del archivo."""
    ruta = tmp_path / "estado.json"
    ruta.write_text(
        '{"ID_SECRETO_98765": {"titulo": "Titulo Reconocible XYZ", '
        '"apikey": "abc", "logintoken": "zzz"',
        encoding="utf-8",
    )
    with caplog.at_level(logging.WARNING, logger="bot_moodle.state"):
        StateStore(ruta)
    warns = _warns_state(caplog)
    assert len(warns) == 1
    msg = warns[0]
    assert "ID_SECRETO_98765" not in msg
    assert "Titulo Reconocible XYZ" not in msg
    for prohibido in ("apikey", "session", "password", "logintoken"):
        assert prohibido not in msg.lower(), f"fuga de secreto en el log: {prohibido}"


def test_estado_es_de_solo_lectura_y_no_se_recalcula_al_guardar(tmp_path):
    """La clasificacion describe como arranco la corrida, no como sigue."""
    store = StateStore(tmp_path / "estado.json")
    with pytest.raises(AttributeError):
        store.estado = "ok"
    store.mark_seen("1", NOW, NOW)
    assert store.estado == "ausente"  # no se recalcula al guardar
    assert StateStore(tmp_path / "estado.json").estado == "ok"  # la proxima carga sí


# --- Reintento del digest pendiente (D8): clave reservada __meta__ ---


def test_digest_pendiente_por_defecto_false(tmp_path):
    assert StateStore(tmp_path / "e.json").digest_pendiente is False


def test_digest_pendiente_se_persiste_bajo_meta_y_se_limpia(tmp_path):
    ruta = tmp_path / "e.json"
    store = StateStore(ruta)
    store.mark_seen("56812", NOW)
    store.mark_digest_pendiente()

    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert data["__meta__"] == {"digest_pendiente": True}
    assert data["56812"]["visto"] == NOW.isoformat(), "el resto del archivo no cambia"
    assert StateStore(ruta).digest_pendiente is True

    store2 = StateStore(ruta)
    store2.clear_digest_pendiente()
    assert store2.digest_pendiente is False
    assert StateStore(ruta).digest_pendiente is False
    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert "__meta__" not in data, "sin digest pendiente el archivo vuelve a su forma previa"
    assert data["56812"]["visto"] == NOW.isoformat()
    assert store2.is_new("56812") is False


def test_meta_convive_con_los_registros_y_no_es_un_registro(tmp_path):
    ruta = tmp_path / "e.json"
    store = StateStore(ruta)
    store.mark_digest_pendiente()
    assert store.is_new("56812") is True, "la clave reservada no cuenta como entrega vista"

    store.mark_seen("56812", NOW)
    data = json.loads(ruta.read_text(encoding="utf-8"))
    assert data["__meta__"] == {"digest_pendiente": True}
    assert data["56812"]["visto"] == NOW.isoformat()
    assert [k for k in data if not k.isdigit()] == ["__meta__"], "un solo prefijo reservado"


def test_archivo_viejo_sin_meta_es_tolerante(tmp_path):
    """estado.json previo a este change: no tiene __meta__ y debe seguir funcionando."""
    ruta = tmp_path / "e.json"
    ruta.write_text(
        json.dumps({"56812": {"visto": NOW.isoformat(), "notificado_urgente": False}}),
        encoding="utf-8",
    )
    store = StateStore(ruta)
    assert store.digest_pendiente is False
    assert store.is_new("56812") is False
    assert store.is_new("1") is True


@pytest.mark.parametrize(
    "meta",
    ["x", None, [], 5, {"otra_cosa": 1}],
    ids=["texto", "null", "lista", "numero", "dict_sin_flag"],
)
def test_meta_corrupto_no_revienta_y_se_puede_reescribir(tmp_path, meta):
    ruta = tmp_path / "e.json"
    ruta.write_text(
        json.dumps({"__meta__": meta, "56812": {"visto": NOW.isoformat()}}),
        encoding="utf-8",
    )
    store = StateStore(ruta)
    assert store.digest_pendiente is False, "un __meta__ ilegible no enciende el reintento"
    assert store.is_new("56812") is False
    store.mark_digest_pendiente()
    assert StateStore(ruta).digest_pendiente is True
    assert StateStore(ruta).is_new("56812") is False


def test_estado_solo_con_meta_conserva_el_flag(tmp_path, caplog):
    """Un digest fallido sin candidatas deja el archivo con __meta__ y nada mas."""
    ruta = tmp_path / "e.json"
    ruta.write_text(json.dumps({"__meta__": {"digest_pendiente": True}}), encoding="utf-8")
    with caplog.at_level(logging.WARNING, logger="bot_moodle.state"):
        store = StateStore(ruta)
    assert store.estado == "ok", "el archivo lo escribio el bot: no es una perdida"
    assert store.digest_pendiente is True
    assert _warns_state(caplog) == []


def test_doc_estado_describe_el_digest_pendiente():
    doc = Path(__file__).resolve().parent.parent / "docs" / "estado.md"
    texto = doc.read_text(encoding="utf-8")
    assert "`__meta__`" in texto
    assert "digest_pendiente" in texto
    assert "reintenta" in texto.lower()


def test_doc_estado_describe_clasificacion_y_accion():
    """El operador tiene que poder leer el log y saber que hacer sin abrir el VPS."""
    doc = Path(__file__).resolve().parent.parent / "docs" / "estado.md"
    assert doc.exists(), "falta docs/estado.md"
    texto = doc.read_text(encoding="utf-8")
    for valor in ("ausente", "vacio", "corrupto", "ok"):
        assert f"`{valor}`" in texto, f"el doc no describe el valor {valor}"
    assert "accion=arranca_con_estado_vacio_puede_renotificar" in texto
    assert "/data" in texto and "volumen" in texto.lower()
    assert "operador" in texto.lower()
