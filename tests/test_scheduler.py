"""10.1: dos jobs diarios 8:00 y 20:00 (lunes 8:00 = digest + vigia)."""

from bot_moodle.scheduler import build_scheduler

runs = []


def _tick():
    runs.append(1)


def test_hay_dos_jobs_diarios_8_y_20():
    sched = build_scheduler(_tick)
    jobs = {j.id: j for j in sched.get_jobs()}
    assert set(jobs) == {"manana", "noche"}
    manana = str(jobs["manana"].trigger)
    noche = str(jobs["noche"].trigger)
    assert "hour='8'" in manana and "minute='0'" in manana
    assert "hour='20'" in noche and "minute='0'" in noche


def test_scheduler_no_dispara_solo_al_crearlo():
    build_scheduler(_tick)
    assert runs == []
