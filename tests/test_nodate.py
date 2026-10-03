"""4.2: sin fecha parseable => descarte silencioso (no aparece, no error)."""

from pathlib import Path

from bot_moodle.dates import parse_activity_dates
from bot_moodle.filters import drop_without_due

FIX = Path(__file__).parent / "fixtures"


def test_bd2_u4_sin_fecha():
    parsed = parse_activity_dates((FIX / "assign_bd2_tp_u4_56812.html").read_text(encoding="utf-8"))
    assert parsed == {"start": None, "due": None}


def test_met_u6_sin_fecha():
    parsed = parse_activity_dates((FIX / "assign_met_u6_1581.html").read_text(encoding="utf-8"))
    assert parsed == {"start": None, "due": None}


def test_fastapi_sin_fecha():
    parsed = parse_activity_dates((FIX / "assign_fastapi_1384.html").read_text(encoding="utf-8"))
    assert parsed == {"start": None, "due": None}


def test_sin_fecha_no_aparece_ni_genera_error():
    cands = [
        {"id": "1", "due": None},
        {"id": "2", "due": None},
    ]
    assert drop_without_due(cands) == []
