"""Envio WhatsApp via Evolution API: un POST por mensaje, sin reintento ciego."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class SendResult:
    ok: bool
    error: str = ""


class EvolutionSender:
    """POST /message/sendText/{instance} con JID + texto. Ante sesion caida reporta y no reintenta."""

    def __init__(self, base_url: str, api_key: str, group_jid: str, instance: str, http: Any = None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.group_jid = group_jid
        self.instance = instance
        self._http = http

    def _http_client(self) -> Any:
        if self._http is not None:
            return self._http
        import requests

        return requests

    def send_text(self, text: str, jid: Optional[str] = None, timeout: int = 20) -> SendResult:
        dest = jid or self.group_jid
        try:
            resp = self._http_client().post(
                self.base_url + f"/message/sendText/{self.instance}",
                headers={"apikey": self.api_key, "Content-Type": "application/json"},
                json={"number": dest, "text": text},
                timeout=timeout,
            )
            if 200 <= resp.status_code < 300:
                logger.info("enviado a %s (%s)", dest, resp.status_code)
                return SendResult(ok=True)
            msg = f"Evolution devolvio {resp.status_code}: {(resp.text or '')[:200]}"
            logger.warning(msg)
            return SendResult(ok=False, error=msg)
        except Exception as exc:
            msg = f"sesion/envio fallido (sin reintento): {exc}"
            logger.warning(msg)
            return SendResult(ok=False, error=msg)
