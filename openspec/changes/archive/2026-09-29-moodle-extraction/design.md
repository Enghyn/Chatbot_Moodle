# Design

## Context

Ver proposal.md (Why) y specs/moodle-extraction/spec.md (contrato). Estado verificado con 8 HTML reales: 4 vistas `Tema_` (una sección) + 4 detalles `assign/view.php?id=`. Security keys deshabilitadas en ambos campus; login nativo user+pass sin captcha. Cursos: Inglés (id 743) + BD2 (id 723) en `campusvirtual.frm.utn.edu.ar`; Prog3 (id 14) en `campustest.frm.utn.edu.ar`. Metodología excluida.

## Goals / Non-Goals

**Goals:**
- Pipeline semanal: login x2 → recorrer secciones → parsear `activity-dates` → filtros temporal/comisión → modelo agrupado listo para formateo WhatsApp.
- Vigía urgente 2x/día (8:00 y 20:00): detectar entregas nuevas con margen <= 7 días y alertarlas en la misma lista con 🆕; lunes 8:00 hace digest + vigía juntos.
- Un solo parser de fechas ES con alias por campus.
- Filtro comisión configurable por curso + exclusion list.
- Estado persistente visto/notificado por `assign id` para no repetir alertas.
- Entrega WhatsApp A2: Evolution API en Docker + app Python en el mismo VPS.

**Non-Goals:**
- Formato final del mensaje y semana vacía (último thread pendiente).
- Cuenta fantasma o admin (se usa cuenta estudiante propia).
- API/token Moodle (descartado hasta habilitación).
- Detección de cambios de fecha en entregas ya notificadas (V2; V1 solo detecta ids nuevos).

## Decisions

### 1. Scraping con sesión (no API)
Por qué: `Security keys` deshabilitadas; `login/token.php` no verificado y admin inalcanzable. Login POST a `/login/index.php` con `logintoken` + cookies es el único camino universal hoy.
Alternativas: API con token pedido a admin (rechazado por costo organizativo); browser automatizado (innecesario sin SSO/captcha).
Evidencia: `div[data-region=activity-dates]` trae fechas cuando el docente las carga (Inglés `Abrió/Cierra`, UML `Apertura/Cierre` mismo selector).

### 2. Recorrido por secciones vía índice, no vista Tema puntual
Por qué: cada `Tema_*.html` solo renderiza 1-4 actividades de la sección actual; el resto son solo títulos en `.courseindex-section-title`, `a.nav-link[title]`, `option[value*=section=]`.
Enfoque: curso completo → enumerar secciones (drawer + tabs) → GET por sección → `li.activity-wrapper.modtype_assign|quiz` → `div[data-activityname]` + `span.instancename` + link `id=`.
Alternativa (calendario-first): descartada como única fuente — Metodología lo trae vacío y en general es parcial con granularidad día.

### 3. Parser de fechas con alias + mapa ES, sin datetime
Selector único: `div[data-region=activity-information] > div[data-region=activity-dates].activity-dates > div > strong + texto`.
Normalización: inicio = `Apertura|Abrió|Abre`; fin = `Cierre|Cierra|Vence|Fecha.*entrega|Fecha límite`. Formato `weekday, DD de month de YYYY, HH:MM` con mapa ES; sin `datetime`/epoch en el markup (verificado por grep negativo).
Decisión de alcance: sin fecha → descartar (ej. BD2-U4 id=56812, Met id=1581, FastApi id=1384 tienen `activity-dates` vacío y `submissionstatustable` sin fecha).

### 4. Filtro comisión = nombre + exclusion list, default inclusivo
Por qué: visibilidad NO filtra (usuario ve y puede entregar en UML de Com1 id=1457 y en el propio 2prog3/2prog4). Caso Yácomo en BD2 sí es `availabilityinfo.isrestricted` sin link → se salta por ausencia de link.
Regla: Inglés sin filtro; BD2/Prog con include-alias (`comision4|c4|2prog4|COM4|com 4`, compartidas con 4) y exclude-alias (`2prog3 solo|Yácomo|Com1`); sin marca → incluir salvo exclusion list por id/título exacto (UML-1457).
Alternativa (default exclusivo): rechadada — rompería generales como FastApi.

### 5. Agrupación verbatim + orden temporal global
Claves: Curso > texto sección tal cual (`Unidad 3`, `Modulo 2 (Joins)`, `UNIDAD 1: FASTAPI` duplicada) > apartado descubierto por breadcrumb (`Práctica 💻`, `Actividades 🚀`). Programación no ordenable por número → orden final solo por fecha fin ascendente; omitir apartados/secciones vacías.

### 6. Vigía urgente con estado (digest + watcher)
Por qué: el digest semanal pierde entregas subidas entre lunes con vencimiento antes del próximo lunes (ej. suben mar, vence mié → nunca se avisa; suben mar, vence mar+7 → el lunes llega con 1 día).
Enfoque: dos ritmos con el mismo scraper. Digest lunes 8:00 (ventana 14 días). Vigía 8:00 y 20:00 todos los días: para cada entrega CON fecha y NUEVA (id nunca visto), si `vencimiento - hoy <= 7 días` → alerta inmediata con la misma lista ordenada + encabezado `Actualización - N nueva(s)` + 🆕 en las nuevas; si margen > 7 → silencio hasta el lunes; si nada nuevo → silencio total. Estado por `assign id`: `{visto, notificado_urgente, notificado_digest}` para alertar una sola vez.
Costo: ~30-60 requests por corrida, 2x/día = despreciable frente a navegación humana; peor punto ciego baja de ~24h a ~12h.
Alternativas: 1x/día (peor ciego 24h, pierde el caso "vence mañana subido al mediodía hasta la noche previa"); 3x+/cada hora (rendimiento marginal, más ruido de infra).

### 7. Envío WhatsApp A2 (Evolution API + Python en VPS)
Por qué A2 sobre A1 (Baileys directo en Node): el operador domina Python y ya tiene VPS; A2 deja scraper/filtros/scheduler en Python (requests + BeautifulSoup + APScheduler/cron) y encierra el protocolo WhatsApp en Evolution (comunidad grande, panel con QR, reconexión y listado de grupos sin código propio). A1 obligaba a JS justo en el módulo más complejo.
Topología: `[Moodle x2] --scrape--> [Python: filtros + estado.json + exclusion list] --POST /message/sendText--> [Evolution Docker, puerto interno + API key] --> [grupo general]`. Secretos: creds Moodle en env, Evo API key en env, sesión WA en volumen Docker, JID del grupo configurado (obtenido del panel).
Alternativas: Cloud API/Twilio (descartadas: templates aprobados incompatibles con texto libre dinámico + costo, overkill para 1 grupo semanal).
Riesgos: re-vinculación QR periódica → el sender SHALL reportar sesión caída y no reintentar a ciegas; el bot habla con el nombre propio → probar primero en grupo solo-vos antes del general.

### 8. Formato del mensaje (fijo, sin links)
Orden fijo de materias (Programación → BD2 → Inglés) en vez de orden global por urgencia: los estudiantes saben en qué parte del mensaje buscar cada materia; dentro de cada curso, unidades y entregas por fecha ascendente. Fecha corta `vie 10 oct, 23:59` (sem + día + mes + hora; año solo si cambia). Nombres verbatim con emojis de Moodle. Digest: `*Comisión 4 - Vencimientos (lun 6 oct)*`. Actualización: `*Comisión 4 - Actualización: N entrega(s) nueva(s)*` + 🆕 solo en nuevas. Semana vacía (digest): aviso corto `Sin entregas con vencimiento hasta la semana que viene, atento a cambios` (confirma bot vivo; el vigía sigue en silencio si nada nuevo). Sin links en V1: función solo informativa; links en V2 si los piden.

## Risks / Trade-offs

- [Rediseño Moodle rompe selectores] → Mitigación: selectores por `data-region`/`data-activityname` (estables) en vez de clases visuales; job semanal de bajo volumen facilita detectar rotura.
- [Alias de comisión incompletos → notificar de más/menos] → Mitigación: exclusion list versionada + log de decisiones por actividad (incluida/excluida + motivo).
- [Credenciales personales en disco] → Mitigación: env vars, nunca en código; documentar rotación (cambio de password rompe ambas sesiones por secreto compartido).
- [Docentes no cargan fecha / cambian convención] → Aceptado: sin fecha no se notifica (decisión de alcance).
- [`campustest` vs `campusvirtual` distintas versiones] → Mitigación: alias ya absorben diferencia observada; validar con 1 positivo más por campus a futuro.
- [Vencidas con entrega tardía abierta (`Agregar entrega` aun overdue)] → Se excluyen igual por fecha (regla: vencida = fuera del mensaje siguiente).
- [Vigía sin estado repite alertas a diario] → Mitigación: estado persistente por id; cada urgente se alerta una sola vez al descubrirse.
- [Vigía ruidoso si reenvía lista completa 2x/día] → Mitigación: silencio total si nada nuevo; encabezado `Actualización` distinto al digest para no parecer duplicado.

## Migration Plan

Sin despliegue (change de captura). Handoff: `/opsx-propose` para tareas de implementación o nuevo change para capa WhatsApp/scheduling.

## Open Questions

- Lista completa de alias de profesores por comisión (Yácomo y otros): completar al implementar.
