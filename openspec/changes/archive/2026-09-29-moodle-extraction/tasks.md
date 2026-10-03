# Tasks

## 1. Setup del proyecto Python

- [x] 1.1 Crear scaffold (`pyproject.toml`, `src/bot_moodle/`, `tests/`, `.env.example` con `MOODLE_C1_URL/USER/PASS`, `MOODLE_C2_URL/USER/PASS`, `EVO_BASE_URL/API_KEY`, `GROUP_JID`, `TEST_GROUP_JID`) y verificar que `python -c "import bot_moodle"` funciona
- [x] 1.2 Fijar dependencias (`requests`, `beautifulsoup4`, `lxml`, `apscheduler` o cron del sistema, `pytest`) y verificar que `pip install -e .` y `pytest --collect-only` corren sin errores
- [x] 1.3 Inventariar los 8 HTML de evidencia como fixtures (`tests/fixtures/`: 4 vistas `Tema_` + BD2-TP-U4 id=56812 + Met-U6 id=1581 + FastApi id=1384 + UML id=1457) y verificar que cada fixture documenta curso, sección y si tiene fecha o no

## 2. Sesión y login Moodle x2 campus

- [ ] 2.1 Implementar login POST a `/login/index.php` con `logintoken` + cookies por campus y verificar con corrida manual que ambas sesiones quedan válidas (doc: comando ejecutado y resultado observado)
- [x] 2.2 Implementar reporte de campus fallido sin abortar el otro (datos parciales nunca se presentan como completos) y verificar con credencial inválida simulada que el ciclo continúa y loguea el fallo

## 3. Recorrido de secciones y extracción de actividades

- [x] 3.1 Implementar enumeración de secciones vía índice (`.courseindex-section-title`, `a.nav-link[title]`, `option[value*=section=]`) + GET por sección y verificar contra fixtures que se listan todas las secciones de cada curso (no solo la vista `Tema_` actual)
- [x] 3.2 Implementar extracción de actividades (`li.activity-wrapper` → `div[data-activityname]` + `span.instancename` + link con `id=`; saltar `isrestricted` sin link como el caso Yácomo) con tests sobre fixtures que verifican: Questionnaire #5 Inglés, TP-U4 BD2 (56812), Entrega-U6 Met (1581), FastApi (1384), UML (1457)
- [x] 3.3 Implementar captura de breadcrumb (curso + sección/apartado: `Práctica`, `Actividades 🚀`) con tests que verifican verbatim con emojis incluidos

## 4. Parser de fechas ES con alias

- [x] 4.1 Implementar parser de `div[data-region=activity-dates]` con alias inicio (`Apertura|Abrió|Abre`) y fin (`Cierre|Cierra|Vence|Fecha.*entrega|Fecha límite`) + mapa de meses ES, con tests que verifican `Cierra: lunes, 2 de noviembre de 2026, 23:59` (Inglés) y `Cierre: martes, 25 de agosto de 2026, 00:00` (UML) normalizados a datetime
- [x] 4.2 Implementar descarte silencioso sin fecha (activity-dates vacío: BD2-U4, Met-U6, FastApi) con tests que verifican que no aparecen ni generan error

## 5. Filtro temporal y orden

- [x] 5.1 Implementar ventana 14 días + exclusión de vencidas + orden ascendente por fecha fin, con tests de reloj fijo que verifican: incluye 3 días, excluye 20 días, excluye UML vencido 25 ago evaluado 29 sept, ordena 3 candidatas
- [x] 5.2 Documentar en `docs/filtros.md` la regla temporal con los 3 casos verificados y verificar que los ejemplos del doc coinciden con los tests

## 6. Filtro de comisión por nombre + exclusion list

- [x] 6.1 Completar la lista de alias (comisión 4: `comision4|c4|2prog4|COM4|com 4`; otras: `2prog3 solo|Yácomo|Com1`) y la exclusion list por id/título exacto (UML id=1457 Com1), con tests que verifican: incluye `COM4,COM3,COM1` / `Com3 y Com4` / `2prog3 y 2prog4`, excluye solo-otra, incluye sin marca, excluye UML-1457
- [x] 6.2 Implementar bypass de filtro para Inglés (todo entra) con test que verifica que ninguna actividad de Inglés se filtra por comisión

## 7. Agrupación y formato del mensaje

- [x] 7.1 Implementar agrupación Curso > Sección-verbatim > Apartado-verbatim con omisión de vacíos, con tests que verifican: apartado sin candidatas no muestra encabezado, `UNIDAD 1: FASTAPI` duplicada se muestra tal cual
- [x] 7.2 Implementar plantilla con orden fijo (Programación → BD2 → Inglés), fecha corta (`vie 10 oct, 23:59`), encabezados digest/actualización/vacío y sin links, con tests que verifican byte-a-byte los 3 ejemplos del design (digest, actualización con 🆕, aviso `Sin entregas con vencimiento hasta la semana que viene, atento a cambios`)

## 8. Vigía urgente con estado

- [x] 8.1 Implementar estado persistente por `assign id` (`{visto, notificado_urgente, notificado_digest}` en `estado.json`) con tests que verifican: id nuevo se registra con timestamp, id conocido no se re-trata como nuevo
- [x] 8.2 Implementar umbral 7 días + silencio sin novedades + alerta única, con tests de reloj fijo que verifican los 3 casos (margen 1 alerta, margen 7 alerta, margen 10 espera al lunes) y que una urgente ya alertada no se re-alerta

## 9. Envío WhatsApp vía Evolution API

- [ ] 9.1 Levantar Evolution API en Docker en el VPS (imagen pineada, API key, volumen de sesión, puerto interno) y verificar que el panel responde y muestra estado de sesión
- [ ] 9.2 Implementar sender (POST `/message/sendText` con JID + texto, registro éxito/fracaso, sin reintento en bucle ante sesión caída) y verificar con envío real al grupo de prueba solo-propio que el mensaje llega con formato intacto
- [ ] 9.3 Documentar en `docs/whatsapp.md` el runbook de pairing QR y re-vinculación y verificar que los pasos documentados funcionan tal cual en una re-vinculación de prueba

## 10. Scheduling, deploy e integración

- [x] 10.1 Configurar scheduler 8:00 y 20:00 diario (lunes 8:00 = digest + vigía) con secretos solo en env y verificar con corrida dry-run que el ritmo dispara y no envía nada cuando no hay novedades
- [ ] 10.2 Corrida end-to-end en modo prueba (scrape real → filtros → envío al grupo de prueba) y verificar que el mensaje respeta orden fijo, omite vacíos/sin fecha/vencidas/comisiones ajenas y marca 🆕 solo en nuevas
- [ ] 10.3 Checklist de pase al grupo general (JID final configurado, sesión estable 48h, exclusion list revisada) y verificar cada ítem marcado antes del primer envío real
