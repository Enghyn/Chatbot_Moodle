# Reglas de Negocio

Cada regla tiene código único para trazabilidad. Fuente: specs en `openspec/specs/` + `docs/filtros.md`.

## Dominio: Extracción (RN-EXT)

- **RN-EXT-01**: Solo son candidatas actividades CON link; las `isrestricted` sin link (ej. agrupamiento Yácomo) se excluyen — porque Moodle ya las bloquea para el usuario.
- **RN-EXT-02**: Solo cuentan entregas con fecha de cierre parseable en `div[data-region=activity-dates]`; sin fecha se descartan (default NO-notificar) **pero el descarte queda registrado en un `warning`** con id, título, modtype, curso, sección y motivo (`sin_fecha`, `sin_id`, `detalle_fallo`, `seccion_fallo`, `sin_sesion`). El descarte nunca es silencioso. Cada corrida cierra con un resumen: secciones, actividades, candidatas, descartes por motivo y duración.
- **RN-EXT-03**: Alias de cierre: `Cierre|Cierra|Vence|Fecha.*entrega|Fecha límite`; alias de inicio (`Apertura|Abrió|Abre`) se ignoran para vencimiento.
- **RN-EXT-04**: Se recorren TODAS las secciones (índice drawer + tabs); la vista `Tema_&section=` de una sección no basta. El nombre de la tab no acota el alcance: dos secciones con el mismo título se recorren ambas.
- **RN-EXT-05**: Nombres de sección y apartado siempre verbatim (con emojis); Programación no se ordena ni normaliza por número.

### Identidad de la actividad

- **RN-EXT-06**: El identificador de una actividad es su **course module id**, tomado por prioridad de fuentes del DOM: (1) `data-id` / `id="module-<N>"` del `li.activity-wrapper`, (2) `mod/*/view.php?id=<N>` de un link del contenedor, (3) ancla `course/view.php?...#module-<N>`. **Nunca** del parámetro `id` de una URL `course/view.php`, que es el id del curso. Sin ninguna fuente válida la actividad se descarta con motivo `sin_id` y queda registrada.

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

- **RN-URG-01**: Solo los ids nunca vistos pueden disparar alerta (conocidos los cubre el digest). El **avistaje** (`visto`, y `cierre_base` en el primer avistaje) se persiste siempre que la corrida procese la candidata, haya enviado o no; lo que la corrida **no** envía (fuera del margen de 7 días, o migración sin base) se marca visto de inmediato. Excepción explícita: las candidatas del mensaje urgente que **sí** se envió y falló quedan pendientes de reintento en vez de vistas, para que la corrida siguiente repita el mismo aviso con su marca `🆕 NUEVA` intacta.
- **RN-URG-02**: Umbral 7 días: `vencimiento - hoy ≤ 7` → alerta inmediata; mayor → espera al lunes.
- **RN-URG-03**: Cada urgente se alerta una sola vez; vigía sin novedades = silencio total, salvo que haya un **digest pendiente** (RN-URG-06), que siempre se reintenta. La marca de **notificación** (`notificado_urgente`, `notificado_digest` y la actualización de `cierre_base`) se persiste sólo tras un envío exitoso (`ok=True`, o `--dry-run`, que se mantiene equivalente): si el envío falla, la corrida siguiente reintenta el mismo aviso.
- **RN-URG-04**: Si una entrega ya conocida cambia su fecha de cierre (comparación por día/mes/hora, año ignorado), se re-notifica en la próxima corrida 8:00/20:00 con la marca `fecha de entrega modificada` y se actualiza la base de comparación **sólo tras el envío exitoso**; cambios solo de año no re-notifican.
- **RN-URG-05**: La carga del estado persistido se clasifica como `ausente` (el archivo no existe), `vacio` (existe pero está en blanco o sin registros, incluido `{}`), `corrupto` (no decodifica, falla la lectura, o decodifica a algo que no es un objeto) u `ok`. Toda clasificación distinta de `ok` emite un `WARNING` de una línea con `estado=`, `ruta=` y `motivo=` (sin contenido ni secretos) y la corrida **envía igual**: estado perdido ≠ silencio. Es distinto de RN-GLB-01: acá el dato del campus **sí** se leyó, lo que se perdió es la memoria de lo ya avisado, y el costo de un aviso de más es menor que el de una entrega perdida.
- **RN-URG-06**: Si el envío del digest (el del lunes 8:00 o su reintento) falla, el digest queda **pendiente** en `estado.json` bajo la clave reservada `__meta__` (`{"digest_pendiente": true}`; nunca colisiona con un `assign id`, que es numérico). La corrida siguiente —8:00 o 20:00, del día que sea— reintenta el **digest completo** (todas las candidatas de la ventana, con el texto de `format_digest`, sin marcas `🆕`), en un único envío; el avistaje de esas candidatas sigue siendo incondicional y `notificado_digest`/`cierre_base` siguen condicionados a `ok=True`. El pendiente se limpia recién tras un envío exitoso (o `--dry-run`) y la clave desaparece del archivo; un reintento fallido lo mantiene encendido para la corrida siguiente. Prioriza el aviso por sobre el silencio (mismo criterio que RN-URG-05) sin volver a la ráfaga de `🆕`.

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
