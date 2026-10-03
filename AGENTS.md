# bot-moodle — Instrucciones para Agentes

Bot personal que avisa por WhatsApp los vencimientos de Moodle de la comisión 4 (3 cursos, 2 campus): digest semanal + vigía urgente 2x/día, filtrado por fecha y comisión, envío vía Evolution API desde VPS.

## Stack Tecnológico

| Capa | Tecnologías | Versión mínima |
|------|--------------|----------------|
| Lenguaje | Python | 3.11 |
| Scraping | requests, BeautifulSoup4 + lxml | requests 2.31, bs4 4.12, lxml 5.0 |
| Scheduling | APScheduler (o cron del sistema) | 3.10 |
| Tests | pytest | 8.0 |
| Envío WhatsApp | Evolution API (Docker, imagen pineada) | ver `docker-compose.evolution.yml` |
| Estado | `estado.json` en disco (sin base de datos) | — |
| Deploy | VPS propio + cron/systemd | — |

## Base de Conocimiento

Leer antes de cualquier change:

- [knowledge-base/README.md](knowledge-base/README.md) — índice y resumen ejecutivo
- [knowledge-base/01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) — propósito, alcance v0.1, fuera de alcance
- [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md) — stack, arquitectura, integraciones
- [knowledge-base/03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) — operador, compañeros, profesores, admins
- [knowledge-base/04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) — Entrega, RegistroEstado, Corrida, Mensaje
- [knowledge-base/05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) — RN-EXT/TMP/COM/URG/ENV/FMT/GLB
- [knowledge-base/06_funcionalidades.md](knowledge-base/06_funcionalidades.md) — épicas y US-001 a US-006
- [knowledge-base/07_flujos_principales.md](knowledge-base/07_flujos_principales.md) — digest, vigía, sesión caída, go-live
- [knowledge-base/08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) — patrones, árbol, seguridad, env vars
- [knowledge-base/09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) — DD-01 a DD-08, SU-01 a SU-04
- [knowledge-base/10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) — ⚠️ leer primero: 2 preguntas altas abiertas (alias de profesores, verificaciones vivas del VPS)

## Skills Disponibles

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| Scraper | Extracción y selectores Moodle | `just-scrape`, `playwright-cli` |
| Testing | Tests pytest + TDD | `python-testing-patterns` |
| Debugging/Ops | Diagnóstico en vivo (sesión, scheduler) | `systematic-debugging` |
| Orquestación | Fundaciones OPSX (globales) | `kb-creator`, `roadmap-generator`, `agents-md-generator` |

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo).

## Roadmap de Changes

Ver [CHANGES.md](CHANGES.md) (índice canónico — leer antes de cada `/opsx-propose`): 10 changes atómicos C-01→C-10, camino crítico C-01→C-02→C-03→C-04→C-05→C-08→C-09→C-10, primer change C-01. Ya archivados: `2026-09-29-moodle-extraction`, `2026-10-01-date-change-watch` (ver `openspec/changes/archive/` y specs en `openspec/specs/`).

## Reglas Duras (específicas del proyecto)

Sin `~/.claude/CLAUDE.md` global en esta máquina: este archivo es la única fuente de reglas (universales + proyecto).

1. **NUNCA** credenciales ni secrets en código, logs o mensajes → **solo** env vars (`.env` fuera del repo).
2. **NUNCA** inventar fechas ni comisiones ante dato ausente o ilegible → default NO-notificar.
3. **NUNCA** reintentar envíos WhatsApp en bucle ante sesión caída → reportar + re-vinculación manual.
4. **NUNCA** tocar un change archivado → las extensiones van en change nuevo.
5. **Siempre** TDD con fixtures HTML reales: test rojo primero antes de cambiar scraper, filtros o formato.
6. **Siempre** selectores por `data-region`/`data-activityname`, nunca por clases visuales de Moodle.
7. **Siempre** suite `pytest` en verde antes de dar por hecha una tarea.
8. **Siempre** un envío por corrida al grupo como máximo; silencio total si el vigía no encuentra novedades.

## Flujo de Trabajo

KB → CHANGES.md → `/opsx:propose <change>` → `/opsx:apply` → `/opsx:archive` (con sync de specs). Fundaciones: `/active-orchestrator:kb|rules|find-skill|registry` para regenerar partes.
