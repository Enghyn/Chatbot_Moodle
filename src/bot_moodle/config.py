"""Configuracion por variables de entorno. Sin credenciales en codigo."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CampusConfig:
    name: str
    base_url: str
    username: str
    password: str


@dataclass(frozen=True)
class EvoConfig:
    base_url: str
    api_key: str
    group_jid: str
    instance: str = "bot-moodle"
    test_group_jid: str = ""


@dataclass(frozen=True)
class AppConfig:
    campus_c1: CampusConfig
    campus_c2: CampusConfig
    evo: EvoConfig

    @property
    def campuses(self) -> list[CampusConfig]:
        return [self.campus_c1, self.campus_c2]


def _req(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise ValueError(f"Falta variable de entorno requerida: {name}")
    return value


def from_env() -> AppConfig:
    """Construye la config solo desde env vars (placeholders en .env.example)."""
    return AppConfig(
        campus_c1=CampusConfig(
            name="C1",
            base_url=os.environ.get("MOODLE_C1_URL", "https://campusvirtual.frm.utn.edu.ar"),
            username=_req("MOODLE_C1_USER"),
            password=_req("MOODLE_C1_PASS"),
        ),
        campus_c2=CampusConfig(
            name="C2",
            base_url=os.environ.get("MOODLE_C2_URL", "https://campustest.frm.utn.edu.ar"),
            username=_req("MOODLE_C2_USER"),
            password=_req("MOODLE_C2_PASS"),
        ),
        evo=EvoConfig(
            base_url=os.environ.get("EVO_BASE_URL", "http://localhost:8080"),
            api_key=_req("EVO_API_KEY"),
            group_jid=_req("GROUP_JID"),
            instance=os.environ.get("EVO_INSTANCE", "bot-moodle"),
            test_group_jid=os.environ.get("TEST_GROUP_JID", ""),
        ),
    )
