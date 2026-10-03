"""5.2: docs/filtros.md documenta la regla temporal y coincide con los tests."""

from pathlib import Path

DOC = Path(__file__).parent.parent / "docs" / "filtros.md"


def test_doc_existe_y_cubre_los_3_casos():
    assert DOC.exists(), "falta docs/filtros.md"
    texto = DOC.read_text(encoding="utf-8")
    for caso in ("3 días", "20 días", "25 de agosto de 2026"):
        assert caso in texto, f"el doc no menciona: {caso}"
    assert "14" in texto  # ventana de 14 días


def test_doc_coincide_con_comportamiento_testeado():
    from datetime import datetime

    from bot_moodle.filters import filter_window

    now = datetime(2026, 9, 29, 8, 0)
    # los mismos 3 casos del doc, verificados contra el codigo
    assert len(filter_window([{"id": "a", "due": datetime(2026, 10, 2, 23, 59)}], now)) == 1
    assert filter_window([{"id": "b", "due": datetime(2026, 10, 19, 23, 59)}], now) == []
    assert filter_window([{"id": "1457", "due": datetime(2026, 8, 25, 0, 0)}], now) == []
