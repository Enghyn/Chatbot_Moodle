# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Scraping con sesión en vez de API
**Decisión**: login POST + parseo HTML. **Contexto**: Security keys deshabilitadas, admin inalcanzable. **Alternativas**: token pedido a admin, browser automatizado. **Justificación**: único camino universal con login nativo sin captcha. **Trade-offs**: frágil ante rediseños; mitigado con selectores `data-region`.

### DD-02 — Evolution API + Python (A2) en vez de Baileys directo (A1)
**Decisión**: protocolo WA encerrado en Evolution Docker; lógica en Python (skill del operador). **Alternativas**: todo-Node con Baileys (obligaba a JS en el módulo más complejo). **Trade-offs**: dos piezas + ~500 MB RAM en VPS.

### DD-03 — Filtro comisión por nombre, default inclusivo + exclusion list
**Decisión**: visibilidad no filtra (el usuario puede entregar en el UML de Com1). Sin marca → entra, salvo exclusion explícita (UML id=1457). **Alternativas**: default exclusivo (rompía generales como FastApi).

### DD-04 — Orden fijo Prog→BD2→Inglés (no global por urgencia)
**Decisión**: predecibilidad para el lector sobre orden perfecto por fecha. Dentro de cada curso sí va ascendente.

### DD-05 — Vigía 2x/día con umbral 7 y estado single-shot
**Decisión**: digest lunes + watcher 8:00/20:00; alerta una sola vez por id nuevo. Peor punto ciego ~12h con costo ~30-60 requests por corrida.

### DD-06 — Metodología fuera, sin links permanente, semana vacía con aviso, fecha sin año
**Decisión**: Met nunca carga fechas (se ignora entera); mensajes solo informativos y sin links (descartado el V2 de links); lunes vacío avisa en vez de silenciar (el vigía sí silencia); fecha corta sin año y año ignorado en comparaciones.

### DD-07 — Sin base de datos (`estado.json`)
**Decisión**: el estado son ids + timestamps; SQLite/Postgres sería overkill operativo.

### DD-08 — Detección de cambios de fecha con re-aviso (ex-V2, ahora alcance)
**Decisión**: entra en alcance la detección de cambios de día/mes/hora de cierre en entregas conocidas, con re-notificación en 8:00/20:00 y marca `fecha de entrega modificada`. **Contexto**: antes era non-goal V2; el operador lo pidió al cerrar preguntas abiertas. **Trade-offs**: exige actualizar specs (`moodle-urgent-watch`), design y tasks en un change nuevo (el `moodle-extraction` está archivado y no se toca); el `estado.json` guarda además la fecha base de comparación.

## Supuestos inferidos

### SU-01 — Login nativo estable sin captcha/2FA
**Origen**: exploración (ambos campus hoy). **Riesgo si es falso**: el scraper deja de autenticar. **Cómo validar**: el dry-run 2.1 lo confirma; si aparece captcha/SSO, rediseñar auth.

### SU-02 — `activity-dates` es la única fuente de fechas
**Origen**: 8 HTML analizados. **Riesgo**: docentes que avisan por foro/PDF quedan fuera. **Cómo validar**: muestreo mensual de una entrega por curso.

### SU-03 — Misma password en ambos campus (secreto compartido)
**Origen**: declarado por el operador. **Riesgo**: rotación rompe ambas sesiones a la vez. **Cómo validar**: documentado en runbook; re-test tras cada cambio.

### SU-04 — El grupo general tolera avisos solo-Comisión 4
**Origen**: decisión del operador. **Riesgo**: confusión de otras comisiones. **Mitigación**: encabezado `Comisión 4` siempre presente.
