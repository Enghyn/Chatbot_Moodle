# Reglas de Negocio

Cada regla tiene código único para trazabilidad. Fuente: specs en `openspec/specs/` + `docs/filtros.md`.

## Dominio: Extracción (RN-EXT)

- **RN-EXT-01**: Solo son candidatas actividades CON link; las `isrestricted` sin link (ej. agrupamiento Yácomo) se excluyen — porque Moodle ya las bloquea para el usuario.
- **RN-EXT-02**: Solo cuentan entregas con fecha de cierre parseable en `div[data-region=activity-dates]`; sin fecha se descartan en silencio.
- **RN-EXT-03**: Alias de cierre: `Cierre|Cierra|Vence|Fecha.*entrega|Fecha límite`; alias de inicio (`Apertura|Abrió|Abre`) se ignoran para vencimiento.
- **RN-EXT-04**: Se recorren TODAS las secciones (índice drawer + tabs); la vista `Tema_&section=` de una sección no basta.
- **RN-EXT-05**: Nombres de sección y apartado siempre verbatim (con emojis); Programación no se ordena ni normaliza por número.

## Dominio: Ventana temporal (RN-TMP)

- **RN-TMP-01**: El digest incluye vencimientos no vencidos dentro de 14 días desde la corrida; el borde (exactamente 14 días) entra.
- **RN-TMP-02**: Lo vencido se elimina del mensaje siguiente; lo que vence más allá de 14 días se guarda sin notificar.
- **RN-TMP-03**: Si un campus falla el login, se reporta y se sigue con el otro; los datos parciales nunca se presentan como completos.

## Dominio: Comisiones (RN-COM)

- **RN-COM-01**: Inglés no filtra por comisión (todo lo visible entra).
- **RN-COM-02**: Mención a la 4 (sola o compartida: `COM4,COM3,COM1`, `Com3 y Com4`, `2prog3 y 2prog4`) → INCLUIR.
- **RN-COM-03**: Solo-otra comisión (`2prog3` solo, `Prof Yácomo`, Com1) → EXCLUIR.
- **RN-COM-04**: Sin marca → INCLUIR como general, salvo exclusion list por id/título exacto (hoy: UML id=1457).

## Dominio: Vigía urgente (RN-URG)

- **RN-URG-01**: Solo los ids nunca vistos pueden disparar alerta (conocidos los cubre el digest).
- **RN-URG-02**: Umbral 7 días: `vencimiento - hoy ≤ 7` → alerta inmediata; mayor → espera al lunes.
- **RN-URG-03**: Cada urgente se alerta una sola vez; vigía sin novedades = silencio total.
- **RN-URG-04**: Si una entrega ya conocida cambia su fecha de cierre (comparación por día/mes/hora, año ignorado), se re-notifica en la próxima corrida 8:00/20:00 con la marca `fecha de entrega modificada` y se actualiza la base de comparación; cambios solo de año no re-notifican.

## Dominio: Envío (RN-ENV)

- **RN-ENV-01**: Un envío por mensaje, al grupo (nunca fan-out por miembro ni privados).
- **RN-ENV-02**: Ante sesión Evolution caída: reportar, no reintentar en bucle; re-vinculación manual.
- **RN-ENV-03**: Probar primero en grupo solo-propio (`TEST_GROUP_JID`); el general solo con `GROUP_JID` final.

## Dominio: Formato (RN-FMT)

- **RN-FMT-01**: Orden fijo Programación → BD2 → Inglés; fecha ascendente adentro; materia vacía no aparece. Fecha corta sin año (`vie 10 oct, 23:59`); la hora sí se muestra y sí se registra para comparar cambios.
- **RN-FMT-02**: Encabezados distinguibles: digest `*Comisión 4 - Vencimientos (fecha)*`, urgente `*Comisión 4 - Actualización: N nueva(s)*` + 🆕 solo en nuevas. Etiqueta de vencimiento normalizada a `Cierra:` (decisión permanente, revisable a futuro).
- **RN-FMT-03**: Lunes vacío → aviso corto (`Sin entregas con vencimiento hasta la semana que viene, atento a cambios`); mensajes siempre sin links (solo informativos, sin V2 de links).

## Dominio: Excepciones globales

- **RN-GLB-01**: Ante cualquier dato ausente o ilegible, el default es NO notificar (nunca inventar fechas ni comisiones).
- **RN-GLB-02**: Secretos solo en variables de entorno; jamás en código, logs ni mensajes.
