# Descripción General

## Stack tecnológico

| Capa | Tecnologías | Versión mínima |
|------|--------------|----------------|
| Lenguaje | Python | 3.11 |
| Scraping | requests, BeautifulSoup4 + lxml | requests 2.31, bs4 4.12, lxml 5.0 |
| Scheduling | APScheduler (o cron del sistema) | 3.10 |
| Tests | pytest | 8.0 |
| Envío WhatsApp | Evolution API (Docker, imagen pineada) | ver `docker-compose.evolution.yml` |
| Estado | `estado.json` en disco (sin base de datos) | — |
| Deploy | VPS propio + cron/systemd | — |

## Arquitectura general

```
[Moodle x2 campus] --scrape (requests+bs4, sesión estudiante)--> [Python]
  login → secciones → actividades → activity-dates → filtros
  (temporal 14d, comisión+exclusion, agrupación verbatim)
       → estado.json (vistos/notificados) → formato (orden fijo, fecha corta)
       --POST /message/sendText--> [Evolution API Docker] --> [grupo WA]
  cron 8:00/20:00; lunes 8:00 = digest + vigía
```

Decisiones de alto nivel: scraping con sesión (no hay API habilitada); desacoplar protocolo WhatsApp en Evolution y dejar toda la lógica en Python (skill del operador); sin DB porque el estado es un puñado de ids con timestamps.

## Integraciones externas

| Servicio | Propósito | Tipo |
|----------|-----------|------|
| Moodle Campus 1 (`campusvirtual.frm.utn.edu.ar`) | Fuente de entregas Inglés + BD2 | Scraping HTML con sesión (POST login + GET) |
| Moodle Campus 2 (`campustest.frm.utn.edu.ar`) | Fuente de entregas Programación | Scraping HTML con sesión (POST login + GET) |
| Evolution API (localhost VPS) | Envío de mensajes WhatsApp | REST interno (`POST /message/sendText`) |

## API REST (si aplica)

No expone API pública. Endpoints consumidos: `POST /login/index.php` (Moodle, con `logintoken`), `GET /course/view.php`, `GET /mod/assign|quiz/view.php?id=`, `POST <EVO_BASE_URL>/message/sendText` (Evolution).
