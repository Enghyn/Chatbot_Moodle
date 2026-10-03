# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **bot-moodle**.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**

---

## Cómo usar este documento

1. Identificar el change a implementar (verificar que sus dependencias están en `openspec/changes/archive/`).
2. Leer los docs de la knowledge-base indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Al terminar el change, archivarlo con `/opsx:archive <nombre-del-change>`.
5. Marcar el checkbox `[x]` en este archivo.

---

## Árbol de dependencias

```
C-01 foundation-setup
  └── C-02 moodle-session                 ← desbloquea TODO lo demás
        └── C-03 scrape-parse
              └── C-04 filters-comision
                    │
                    ├── C-05 state-watcher-urgent
                    │     └── C-06 date-change-watch    ← paralelo con C-07/C-08
                    │
                    ├── C-07 grouping-formatting        ← paralelo con C-05
                    │
                    └── C-08 whatsapp-delivery          ← paralelo con C-05/C-07
                          └── C-09 cycle-scheduler      ← + C-05 + C-06 + C-07 + C-08
                                └── C-10 deploy-go-live
```

### Paralelismo por fase

> Cada "gate" es un punto de sincronización. Los changes dentro de un grupo pueden ejecutarse en paralelo.

```
GATE 0: ninguna
  → C-01 (solo)

GATE 1: C-01 ✓
  → C-02 (solo)

GATE 2: C-02 ✓
  → C-03 (solo)

GATE 3: C-03 ✓
  → C-04 (solo)

GATE 4: C-04 ✓                     ← PRIMER FORK (3 paralelos)
  → C-05 state-watcher-urgent      [Agente A]
  → C-07 grouping-formatting       [Agente B]
  → C-08 whatsapp-delivery         [Agente C]

GATE 5: C-05 ✓
  → C-06 date-change-watch         [Agente A — si C-05 ✓]

GATE 6: C-05 + C-06 + C-07 + C-08 ✓
  → C-09 cycle-scheduler           (solo)

GATE 7: C-09 ✓
  → C-10 deploy-go-live            (solo)
```

### Camino crítico (8 changes — mínimo irreducible)

```
C-01 → C-02 → C-03 → C-04 → C-05 → C-08 → C-09 → C-10
```

### Plan óptimo con 3 agentes

```
Paso │ Agente A (Extracción)      │ Agente B (Lógica dominio)       │ Agente C (Delivery/Ops)
─────┼────────────────────────────┼─────────────────────────────────┼─────────────────────────
  1  │ C-01 foundation-setup      │         —                       │         —
  2  │ C-02 moodle-session        │         —                       │         —
  3  │ C-03 scrape-parse          │         —                       │         —
  4  │         —                  │ C-04 filters-comision           │         —
  5  │ C-05 state-watcher-urgent  │ C-07 grouping-formatting        │ C-08 whatsapp-delivery
  6  │ C-06 date-change-watch     │         —                       │         —
  7  │ C-09 cycle-scheduler       │         —                       │         —
  8  │ C-10 deploy-go-live        │         —                       │         —
```

---

## FASE 0 — Cimientos

### [C-01] `foundation-setup`
- **Estado**: `[ ]` pendiente
- **Scope**: Scaffolding completo del CLI Python + infraestructura base (US-001 a US-006 lo referencian)
  - Estructura `src/bot_moodle/` + `tests/` + `docs/` + `knowledge-base/` + `openspec/` según `08_arquitectura_propuesta.md` §Estructura de directorios
  - `pyproject.toml`: Python ≥ 3.11, deps `requests 2.31`, `beautifulsoup4 4.12`, `lxml 5.0`, `apscheduler 3.10`, `pytest 8.0`
  - `config.py`: carga de env vars (`MOODLE_C1_URL`, `MOODLE_C1_USER/PASS`, `MOODLE_C2_URL`, `MOODLE_C2_USER/PASS`, `EVO_BASE_URL`, `EVO_API_KEY`, `GROUP_JID`, `TEST_GROUP_JID`); falla en claro si falta secreto (RN-GLB-02)
  - `.env.example` con las 8 variables y ejemplos (sin secretos reales); `estado.json` en `.gitignore` (runtime, no versionado)
  - `docker-compose.evolution.yml` con imagen Evolution pineada, puerto interno + API key
  - Harness de tests: `tests/fixtures/` (8 HTML + `manifest.json`), `pytest` en verde con 1 smoke test de importación
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/01_vision_y_objetivos.md` (alcance v0.1 y fuera de alcance)
  - `knowledge-base/02_descripcion_general.md` §Stack
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios
  - `knowledge-base/08_arquitectura_propuesta.md` §Variables de entorno

---

## FASE 1 — Extracción Moodle

> C-02 y C-03 son secuenciales (el scrape necesita la sesión). C-04 cierra la fase.

### [C-02] `moodle-session`
- **Estado**: `[ ]` pendiente
- **Scope**: Login dual en ambos campus con fail-open (US-001; RN-EXT-01, RN-TMP-03, RN-GLB-02)
  - `session.py`: adapter de sesión Moodle — `POST /login/index.php` con `logintoken`, una sesión `requests` por campus (misma clave, user+pass distintos por campus)
  - `login_campus(url, user, pass) -> Session` con parseo defensivo del token; credenciales solo desde env, jamás en logs (RN-GLB-02)
  - `login_all() -> (ok: list, fallido: list)`: campus fallido se reporta y NO bloquea al otro (RN-TMP-03); datos parciales nunca se presentan como completos
  - `Corrida.campus_ok / campus_fallido` poblado desde aquí (ver `04_modelo_de_datos.md` §Corrida)
  - Tests: login OK en ambos, un campus caído sigue con el otro, credenciales ausentes fallan en claro, secreto nunca aparece en logs
- **Dependencias**: C-01
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-001
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TMP-03 y §RN-GLB-02
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 pasos 1–2
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (Adapter de sesión, Fail-open)

### [C-03] `scrape-parse`
- **Estado**: `[ ]` pendiente
- **Scope**: Recorrido completo de secciones + extracción de entregas + parseo ES de fechas (US-002; RN-EXT-02 a RN-EXT-05)
  - `sections.py`: recorre TODAS las secciones (índice drawer + tabs) de Inglés, BD2 (Campus 1) y Prog3 (Campus 2); la vista `Tema_&section=` sola no basta (RN-EXT-04)
  - `activities.py`: extrae solo actividades CON link; excluye `isrestricted` sin link (RN-EXT-01)
  - `breadcrumbs.py`: curso/sección/apartado siempre verbatim (con emojis, sin normalizar número de Programación) (RN-EXT-05)
  - `dates.py`: parsea `div[data-region=activity-dates]` con alias ES — cierre (`Cierre|Cierra|Vence|Fecha.*entrega|Fecha límite`), meses ES incl. `setiembre/sep/set`; alias de apertura se ignoran; sin cierre parseable se descarta en silencio (RN-EXT-02, RN-EXT-03, RN-GLB-01)
  - `scrape.py`: pipeline `secciones → actividades → breadcrumbs → dates` que produce `Entrega(assign_id, titulo, curso, seccion, apartado, apertura, cierre)` (ver `04_modelo_de_datos.md` §Entrega)
  - Tests: fixtures 8 HTML — alias Apertura/Cierre, `sep/setiembre`, sin-fecha descartada, `isrestricted` excluida, recorrido multi-sección
- **Dependencias**: C-02
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-002
  - `knowledge-base/04_modelo_de_datos.md` §Entrega
  - `knowledge-base/05_reglas_de_negocio.md` §RN-EXT-01 a RN-EXT-05
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 pasos 3–4

### [C-04] `filters-comision`
- **Estado**: `[ ]` pendiente
- **Scope**: Ventana temporal 14 días + filtro de comisión + exclusion list (US-003; RN-TMP-01/02, RN-COM-01 a 04)
  - `filters.py`: ventana digest — incluye vencimientos no vencidos dentro de 14 días desde la corrida (borde 14 entra); vencidas se eliminan del siguiente; > 14 días se guarda sin notificar (RN-TMP-01, RN-TMP-02; casos `docs/filtros.md`)
  - `comision.py`: Inglés sin filtro (todo visible entra, RN-COM-01); mención a la 4 sola o compartida (`COM4,COM3,COM1`, `Com3 y Com4`, `2prog3 y 2prog4`) → INCLUIR (RN-COM-02); solo-otra (`2prog3` solo, `Prof Yácomo`, Com1) → EXCLUIR (RN-COM-03); sin marca → INCLUIR salvo exclusion list (RN-COM-04)
  - Exclusion list inicial por id/título exacto: `UML id=1457` Comisión 1 (ver `09_decisiones_y_supuestos.md` DD-03/DD-04)
  - Ante dato ausente/ilegible default NO-notificar (RN-GLB-01)
  - Tests: matriz temporal (borde 14, vencida, lejana) + matriz comisión (casos `docs/filtros.md`) + exclusion list
- **Dependencias**: C-03
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-003
  - `knowledge-base/05_reglas_de_negocio.md` §RN-TMP-01/02 y §RN-COM-01 a 04
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-03
  - `knowledge-base/10_preguntas_abiertas.md` §Alias por comisión (exclusion list pre go-live)

---

## FASE 2 — Seguimiento y vigía urgente

> C-05 primero; C-06 lo extiende. C-07 y C-08 corren en paralelo con esta fase (GATE 4).

### [C-05] `state-watcher-urgent`
- **Estado**: `[ ]` pendiente
- **Scope**: Estado single-shot + vigía 2x/día con umbral 7 días (US-004 CA-1/2/3; RN-URG-01/02/03, DD-05, DD-07)
  - `state.py`: `estado.json` en disco (sin DB) — `RegistroEstado[assign_id] = {visto, notificado_urgente, notificado_digest}` 1-a-1 con Entrega (ver `04_modelo_de_datos.md` §RegistroEstado); lectura/escritura atómica, `{}` inicial
  - `watcher.py`: solo ids nunca vistos pueden disparar alerta (RN-URG-01); `vencimiento - hoy ≤ 7` → alerta inmediata en la corrida que la descubre; margen mayor → registra vista y espera al lunes (RN-URG-02); cada urgente se alerta una sola vez (RN-URG-03); vigía sin novedades = silencio total (cero mensajes)
  - El digest del lunes marca vistos pero NO dispara 🆕 (ver `07_flujos_principales.md` §Flujo 1 paso 6)
  - Tests: primer avistaje urgente ≤ 7 alerta, > 7 espera al lunes, re-alerta bloqueada, vigía vacío silencioso, digest no marca 🆕
- **Dependencias**: C-04
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004 (CA-1, CA-2, CA-3)
  - `knowledge-base/04_modelo_de_datos.md` §RegistroEstado y §Mensaje
  - `knowledge-base/05_reglas_de_negocio.md` §RN-URG-01 a 03
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-05 y §DD-07

### [C-06] `date-change-watch`
- **Estado**: `[ ]` pendiente
- **Scope**: Detección de cambios de fecha de cierre en entregas conocidas con re-aviso (US-004 CA-4; RN-URG-04, DD-08)
  - Extiende `watcher.py` + `state.py`: la base de comparación guarda además la fecha base (día/mes/hora; año ignorado)
  - Si un id conocido cambia su día/mes/hora de cierre vs `estado.json` → marca `fecha de entrega modificada`, actualiza la base y re-notifica en la próxima corrida 8:00/20:00; cambios solo de año NO re-notifican (RN-URG-04)
  - Mensaje tipo actualización incluye la marca de modificada donde corresponda (coordina con C-07)
  - Specs nuevas (`moodle-urgent-watch` delta / change dedicado); el archivado `moodle-extraction` NO se toca (ver `10_preguntas_abiertas.md` §Resueltas)
  - Tests: cambio de día re-avisa, cambio de hora re-avisa, cambio solo-año no re-avisa, doble cambio no duplica aviso
- **Dependencias**: C-05
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-004 (CA-4)
  - `knowledge-base/05_reglas_de_negocio.md` §RN-URG-04
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-08
  - `knowledge-base/10_preguntas_abiertas.md` §Resueltas (alcance date-change-watch)

---

## FASE 3 — Formato y envío

> C-07 y C-08 son independientes entre sí (ambos dependen solo de C-04 salvo el contrato de `Mensaje` que coordinan con C-05/C-06). Pueden proponerse en paralelo.

### [C-07] `grouping-formatting`
- **Estado**: `[ ]` pendiente
- **Scope**: Agrupación por materia + plantillas de mensaje distinguibles (US-006; RN-FMT-01/02/03, DD-04, DD-06)
  - `grouping.py`: orden fijo Programación → BD2 → Inglés; fecha ascendente dentro de cada curso; materia vacía no aparece (RN-FMT-01, DD-04)
  - `formatting.py`: fecha corta ES sin año (`vie 10 oct, 23:59`), hora visible; etiqueta de vencimiento normalizada a `Cierra:` (RN-FMT-01, RN-FMT-02); títulos verbatim con emojis; mensajes siempre SIN links (RN-FMT-03, DD-06)
  - Plantillas (`tipo: digest | actualizacion | aviso_vacio`): digest `*Comisión 4 - Vencimientos (fecha)*`; urgente `*Comisión 4 - Actualización: N nueva(s)*` + 🆕 solo en nuevas + marca `fecha de entrega modificada` donde aplique; lunes vacío → aviso corto fijo (RN-FMT-02, RN-FMT-03)
  - Consume `Mensaje{tipo, nuevas, texto}` (ver `04_modelo_de_datos.md` §Mensaje)
  - Tests: orden fijo por materia, fecha corta ES, encabezados por tipo, 🆕 solo en nuevas, aviso vacío exacto, sin links en ningún caso
- **Dependencias**: C-04
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-006
  - `knowledge-base/04_modelo_de_datos.md` §Mensaje
  - `knowledge-base/05_reglas_de_negocio.md` §RN-FMT-01 a 03
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-04 y §DD-06

### [C-08] `whatsapp-delivery`
- **Estado**: `[ ]` pendiente
- **Scope**: Envío al grupo vía Evolution API con política sin-reintentos (US-005; RN-ENV-01/02/03)
  - `sender.py`: adapter Evolution — un `POST <EVO_BASE_URL>/message/sendText` por mensaje al grupo (nunca fan-out ni privados, RN-ENV-01); api key `EVO_API_KEY` desde env (unificar nombre según `10_preguntas_abiertas.md` IN-01)
  - Ante sesión caída: loguea, reporta y NO reintenta en bucle; re-vinculación manual vía panel (logout → nuevo QR → escanea) (RN-ENV-02; `07_flujos_principales.md` §Flujo 3)
  - Destino por env: primero `TEST_GROUP_JID` (grupo solo-propio); general solo con `GROUP_JID` final (RN-ENV-03)
  - Registra éxito/fracaso por corrida para `cycle.py`
  - Tests: un POST por mensaje, payload al JID correcto, fallo de sesión sin reintento, TEST vs GROUP por env
- **Dependencias**: C-04
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-005
  - `knowledge-base/05_reglas_de_negocio.md` §RN-ENV-01 a 03
  - `knowledge-base/07_flujos_principales.md` §Flujo 3
  - `knowledge-base/10_preguntas_abiertas.md` §IN-01 (nombre de key Evolution)

---

## FASE 4 — Orquestación y go-live

### [C-09] `cycle-scheduler`
- **Estado**: `[ ]` pendiente
- **Scope**: Orquestación de corridas + scheduler 8:00/20:00 + CLI operador (Flujos 1, 2, 4)
  - `cycle.py`: pipeline `session → scrape → dates → filters → watcher → grouping → formatting → sender`; tipos de corrida `digest (lunes 8:00)` vs `vigía (8:00/20:00)`; digest siempre produce exactamente un mensaje (o aviso vacío), vigía sin novedades = cero mensajes (ver `04_modelo_de_datos.md` §Corrida)
  - `scheduler.py`: APScheduler (o cron) — lunes 8:00 digest + vigía, resto 8:00/20:00 vigía; lunes 8:00 = digest + vigía combinados
  - `main.py`: CLI `--dry-run` (sin envío, valida IN-02/vivas), `--send-test` (mensaje al grupo de prueba); códigos de salida para cron/systemd
  - Integra C-05/C-06 (estado), C-07 (texto) y C-08 (envío) sin lógica duplicada
  - Tests: digest vacío avisa, vigía vacío silencia, digest marca vistos sin 🆕, vigía urgente envía una vez, `--dry-run` no llama a Evolution
- **Dependencias**: C-05, C-06, C-07, C-08
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 y §Flujo 2
  - `knowledge-base/04_modelo_de_datos.md` §Corrida
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (Pipeline por etapas)
  - `knowledge-base/03_actores_y_roles.md` (operador como único operador del CLI)

### [C-10] `deploy-go-live`
- **Estado**: `[ ]` pendiente
- **Scope**: Deploy en VPS + vinculación WhatsApp + checklist de go-live (Flujo 4; preguntas abiertas de alta prioridad)
  - VPS: Evolution Docker arriba (puerto interno, API key, no expuesto), cron/systemd 8:00/20:00 + lunes 8:00, `.env` real fuera del repo, `estado.json` runtime
  - Vinculación: panel → QR → sesión estable 48h; runbook de sesión caída (`disconnected` → logout → QR → `--dry-run` de validación)
  - Go-live (Flujo 4): checklist — `GROUP_JID` final, sesión 48h estable, exclusion list revisada (alias por comisión más allá de Yácomo), `TEST_GROUP_JID` → `GROUP_JID`; primer digest un lunes 8:00 con observación de recepción y formato
  - Cierre: ejecutar las 6 verificaciones vivas pendientes (2.1, 9.1–9.3, 10.2, 10.3) en el VPS; red de 69 tests en verde
  - Docs: `docs/filtros.md`, `docs/whatsapp.md` (con IN-01 unificada) al día
- **Dependencias**: C-09
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/07_flujos_principales.md` §Flujo 3 y §Flujo 4
  - `knowledge-base/10_preguntas_abiertas.md` (preguntas de alta prioridad + IN-01)
  - `knowledge-base/03_actores_y_roles.md` (operador y superficie expuesta)
  - `knowledge-base/01_vision_y_objetivos.md` §Métricas de éxito
