# Visión y Objetivos

## Propósito del sistema

Avisar automáticamente por WhatsApp los vencimientos de entregas de Moodle a los estudiantes de la comisión 4, para que ninguna entrega con fecha pase por alto entre un digest semanal y el siguiente.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|-------|--------------------|-----------------------|
| Operador (estudiante comisión 4, dueño del número) | Recibir y reenviar avisos sin trabajo manual semanal | Mantener alias de comisión y exclusion list al día; re-vincular la sesión WA cuando caiga |
| Compañeros del grupo general | Ver cada lunes qué vence en 2 semanas y ser alertados de urgencias nuevas | Distinguir a golpe de vista lo nuevo (🆕) de lo ya avisado |
| Profesores | Cargar fechas en Moodle como siempre | Sin acción requerida (el bot solo lee lo que ya cargan) |

## Alcance v0.1

- 3 cursos: Inglés 2, Bases de Datos II (Campus 1) y Programación 3 (Campus 2).
- Scraping con la sesión estudiante propia (comisión 4), login nativo user+pass.
- Solo entregas CON fecha parseable en `activity-dates`; sin fecha = se ignoran.
- Digest semanal lunes 8:00 (ventana 14 días) + vigía urgente 8:00/20:00 (nuevas con margen ≤ 7 días).
- Filtro de comisión por nombre + exclusion list; Inglés sin filtro.
- Envío al grupo general vía Evolution API (sesión personal del número propio).
- Formato fijo: orden Programación → BD2 → Inglés, fecha corta ES, sin links.

## Fuera de alcance

- Metodología de Sistemas (nunca carga fechas — excluida por decisión).
- API/token Moodle (Security keys deshabilitadas en ambos campus).
- Mensajes privados personalizados por alumno; cuenta business/Cloud API/Twilio.
- Detección de cambios de fecha en entregas ya notificadas (V2).
- Links a entregas en el mensaje (V1 solo informativo).

## Métricas de éxito

- Cero entregas con fecha en ventana que no aparezcan en algún mensaje antes de vencer con margen útil.
- Cero alertas repetidas (cada urgente se alerta una sola vez).
- 69 tests en verde como red de seguridad del parser y los filtros.
