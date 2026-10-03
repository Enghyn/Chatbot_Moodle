# Proposal

## Why

El bot de WhatsApp necesita una fuente confiable de vencimientos desde dos campus Moodle con 4 cursos heterogéneos. La exploración con HTML reales demostró que las fechas solo existen cuando el docente carga `activity-dates`, que las comisiones se mezclan por visibilidad y que Programación no tiene orden de unidades. Sin un diseño de extracción cerrado, el bot notificaría de más, de menos o con fechas inventadas.

## What Changes

- Alcance: 3 cursos (Inglés, BD2, Programación). Metodología queda FUERA (nunca carga fechas).
- Identidad: cuenta estudiante propia (comisión 4), login nativo user+pass en 2 campus (usuario distinto, misma clave, sin captcha).
- Extracción por scraping de sesión: recorrer TODAS las secciones (drawer + tabs), no solo la vista `Tema_&section=` actual.
- Solo se notifican entregas CON fecha parseable en `div[data-region=activity-dates]` (alias Apertura/Abrió + Cierre/Cierra/Vence). Sin fecha = descartar.
- Filtro temporal: ventana 2 semanas, orden por urgencia, vencidas se eliminan del mensaje siguiente, futuras >2 semanas se guardan sin notificar.
- Filtro comisión por nombre + lista de exclusión (visibilidad NO alcanza en Programación): Inglés sin filtro; BD2 y Programación con alias de comisión 4 y exclusiones explícitas (ej. UML-1457 = Com1, Yácomo = otra).
- Agrupación Curso > Sección-verbatim > Apartado-verbatim; omitir apartados y secciones vacías; apartados descubiertos dinámicamente (Práctica, Actividades, etc.).
- Vigía urgente: además del digest semanal (lunes, ventana 14 días), corridas diarias 8:00 y 20:00 que detectan entregas NUEVAS con vencimiento dentro de 7 días y las alertan de inmediato en la misma lista con resaltado 🆕; sin novedades = silencio.
- Entrega WhatsApp (opción A2): sesión personal del número propio vía Evolution API en Docker en VPS; app Python (scraper + filtros + scheduler) envía por REST interno al grupo general de alumnos; un envío por mensaje; encabezado con Comisión 4.
- Formato del mensaje: orden fijo de materias (Programación, BD2, Inglés), dentro de cada curso por fecha ascendente; semana vacía = aviso corto ("Sin entregas con vencimiento hasta la semana que viene, atento a cambios"); sin links, solo informativo.
- Security keys / API por token descartadas (deshabilitadas en ambos campus). Plan B API solo si se habilita a futuro.

## Capabilities

### New Capabilities
- `moodle-extraction`: extracción y filtrado de entregas con fecha desde Moodle (login, recorrido de secciones, parseo de fechas ES, filtros temporal y de comisión, agrupación para notificación).
- `moodle-urgent-watch`: detección diaria de entregas nuevas urgentes (umbral 7 días, estado visto/notificado, alerta con resaltado en la misma lista).
- `whatsapp-delivery`: envío de digest y alertas al grupo vía sesión personal Evolution API (pairing QR, un envío por mensaje, encabezado Comisión 4, grupo de prueba primero).
- `message-format`: plantilla del mensaje (orden fijo de materias, fecha corta ES, encabezados digest/actualización/vacío, sin links).

### Modified Capabilities
- (ninguna)

## Impact

- Sistemas: 2 campus Moodle (`campusvirtual.frm.utn.edu.ar`, `campustest.frm.utn.edu.ar`), 3 cursos (IDs observados: Inglés 743, BD2 723, Prog3 14).
- Sin código aún; este change solo captura diseño. La implementación (scraper, scheduler, capa WhatsApp) vive en changes futuros.
- Riesgos: scraping frágil ante rediseños Moodle; credenciales personales en disco (mitigar con env vars); alias de comisión incompletos requieren mantenimiento de lista de exclusión.
