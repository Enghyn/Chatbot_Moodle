# Proposal

## Why

El bot **renotificó** por WhatsApp dos entregas de BD2 (Unidad 7 y Unidad 8, cierre lun 2 nov 00:00) marcadas `🆕 NUEVA` en la corrida de las **08:00** y **otra vez** en la de las **20:00** del 2026-10-28.

La causa raíz está confirmada con evidencia recolectada en producción (contenedor `37d5672fab8b`):

```
printenv ESTADO_PATH  → /data/estado.json        (correcto)
ls -la /data          → vacío, mtime = hora de build de la imagen
cat /data/estado.json → NO EXISTE
cat /app/estado.json  → NO EXISTE
find / -name 'estado.json*' → sin resultados
mount | grep /data    → SIN_MOUNT (no es volumen)
touch /data/_probe    → ESCRITURA_OK
```

**`/data` no es un volumen persistente.** `Dockerfile:25` hace `RUN mkdir -p /data` y `Dockerfile:27` setea `ENV ESTADO_PATH=/data/estado.json`, pero sin un mount en `/data` ese directorio es parte del *writable layer* del contenedor. Cada deploy (o cualquier recreación) arranca con `/data` vacío y el estado se pierde.

Cronología del síntoma:

```
08:00   digest envía las 2 de BD2   → estado escrito en el contenedor A
~21:03  redeploy                    → contenedor A destruido, muere el estado
20:00   contenedor B: state.py:29 ve que el archivo no existe → _data = {}
        is_new() devuelve True para ambas → 🆕 NUEVA otra vez
```

El invariante que explica el síntoma es el mismo en las dos corridas: **una corrida que arranca en un contenedor sin `/data` persistido ve todas las entregas como nuevas y las renotifica**. El diagnóstico de esta causa no se reabre en este change.

**La hipótesis original del usuario quedó refutada**: las entregas "espontáneas" (🆕) **sí** se persisten, con la misma línea `mark_seen` que las de gap (`watcher.py:47-48`). El margen de 7 días decide si se **envía**, no si se **persiste**. Se probó ejecutando dos corridas consecutivas con el mismo `StateStore`: la segunda devuelve `kind="silence"`. O sea: con estado sano el código no puede duplicar.

Lo que sí está mal es que el sistema **no falla en claro** ante esta pérdida y que el propio ciclo de vida del estado puede perder avisos reales:

1. **`state.py:29-33`** — si el archivo no existe, o si no decodifica (`JSONDecodeError`/`OSError`), arranca con `_data = {}` **sin loguear nada**. Un estado perdido y un estado vacío legítimo son indistinguibles en el log.
2. **`watcher.py:47-48`** — `mark_seen` se llama **antes** de enviar, en la misma línea que decide `new_urgent`. Si el envío falla (`ok=False`), el ítem queda `visto=True` y `notificado_urgente=False` → todas las corridas siguientes son silencio: **aviso perdido para siempre**.
3. **`cycle.py:56`** — `if sent or dry_run:` envuelve también el `mark_seen` de avistaje. Si falla el digest del lunes no se persiste nada, y la corrida siguiente encuentra todo nuevo → ráfaga de 🆕.
4. **`state.py:42`** — el `.tmp` tiene nombre fijo (`estado.json.tmp`): dos escritores concurrentes se pisan (uno pisa el `.tmp` del otro y el `os.replace` publica contenido ajeno o falla).

## What Changes

- **Diagnóstico del estado (fallar en claro)**: `StateStore` clasifica la carga del archivo como `ausente` / `vacio` / `corrupto` / `ok`, lo expone como propiedad y emite un `warning` de una línea por carga no sana (ruta incluida, sin contenido del archivo, sin secretos). El comportamiento de envío **no cambia**: estado ausente/vacío/corrupto sigue arrancando con `{}` y **se envía igual** (decisión del usuario: nunca perder un aviso real por precaución). Lo nuevo es que la pérdida se ve en segundos en el log.
- **Campo `estado=` en la línea de cierre de corrida**: se agrega `estado=ausente|vacio|corrupto|ok` al resumen `corrida: ...` que ya existe (`scrape.py:173-192`), para que la pestaña Logs de EasyPanel diga si la corrida arrancó con estado sano.
- **Separar avistaje de notificación**: `visto` = "ya lo vi" (se persiste siempre, haya enviado o no); `notificado_urgente` / `notificado_digest` / `cierre_base` = "ya te avisé" (se persiste **solo tras `ok=True`**, o en `dry_run`, que hoy equivale a un envío exitoso).
- **`partition_urgent` deja de marcar visto lo que va a enviar**: las alertas se marcan `visto` recién después de `ok=True`; las candidatas que no se envían (fuera del margen de 7 días, o sin base en la migración) se siguen marcando `visto` de inmediato, como hoy.
- **El digest fallido se reintenta en la corrida siguiente**: si falla el envío del lunes, las candidatas quedan vistas (no hay ráfaga de 🆕) y `notificado_digest`/`cierre_base` no se tocan, pero se enciende `__meta__.digest_pendiente` en `estado.json`. La corrida siguiente (8:00 o 20:00, del día que sea) reintenta el **digest completo** con `format_digest` tal cual —todas las candidatas de la ventana, sin 🆕— en un único envío, y el flag se limpia recién con el envío exitoso (o `dry_run`). Decisión del usuario: el aviso pesa más que el silencio, sin ráfaga de 🆕 y sin esperar al lunes siguiente.
- **`.tmp` con nombre único por escritura**: `estado.json.<pid>.<uuid>.tmp`, con limpieza del propio temporal si la escritura falla. Dos procesos dejan de pisarse el temporal; `os.replace` sigue siendo la publicación atómica.
- **Tests de dos corridas consecutivas reales**, lectura corrupta y escritores concurrentes, que hoy no existen.

## Fuera de alcance

- **Montar el volumen en `/data` es una acción de infraestructura del operador en EasyPanel, NO forma parte de este change.** El change hace que la pérdida sea visible y que los avisos no se pierdan por el ciclo de vida del estado, pero **no puede persistir el estado por sí solo**: un `Dockerfile` no crea un volumen persistente, y el mount lo configura el operador en el panel del hosting. Sin ese mount, el 🆕 repetido tras un deploy seguirá ocurriendo, pero quedará diagnosticado en segundos (`estado=ausente` en la línea de cierre).
- **No se cambia el formato ni el texto del mensaje de WhatsApp** (decisión previa del usuario): nada de líneas de advertencia dentro del mensaje. Regla dura 8 (un envío por corrida) y formato ya cerrado.
- **No se reescribe el historial de git.**
- No se agrega base de datos, locking entre procesos ni un reloj de expiración del estado.
- No se cambia el margen de 7 días, la ventana de 14 días, los filtros de comisión ni el envío por Evolution API.
- No se toca la semántica de `dry_run` (hoy persiste como un envío exitoso): cambiarla alteraría el comportamiento del comando de verificación sin que el usuario lo haya pedido.
- No se tocan los changes archivados (regla dura 4).

## Capabilities

### New Capabilities

_(ninguna)_ — el subsistema de estado no se separa en una capability propia: su contrato observable (avistaje único, alerta única, single-shot por cambio) es exactamente el del vigía, y duplicarlo en una capability nueva generaría dos fuentes de verdad para la misma garantía.

### Modified Capabilities

- `moodle-urgent-watch`: *Detección de entregas nuevas* (el avistaje se persiste siempre y sobrevive a envíos fallidos; un estado perdido no se confunde con "todo nuevo" sin aviso), *Umbral urgente de 7 días* (las candidatas fuera de margen se marcan vistas de inmediato: al entrar en la ventana no se notifican por primera vez) y *Ritmo 8:00 y 20:00 con digest integrado* (la marca de notificación se persiste solo tras envío exitoso; un envío fallido se reintenta en la corrida siguiente, y un digest fallido se reintenta completo —no como actualización— con el flag `__meta__.digest_pendiente`). Se agrega el requirement *Estado persistente diagnosticable* (carga clasificada, warning, escritura con temporal único).
- `moodle-extraction`: *Solo entregas con fecha parseable* — la línea de cierre de corrida suma el campo `estado=<ausente|vacio|corrupto|ok>`.

## Impact

- **Código**: `src/bot_moodle/state.py` (clasificación de carga + `warning` + `.tmp` único), `src/bot_moodle/watcher.py` (`partition_urgent` deja de marcar visto lo que se va a enviar), `src/bot_moodle/cycle.py` (orden de persistencia por rama digest/update), `src/bot_moodle/scrape.py` (campo `estado=` en `_resumen_cierre`) y `src/bot_moodle/main.py` (pasa el estado del store al scrapeo). Sin cambios en `formatting.py`, `grouping.py`, `filters.py`, `comision.py`, `sender.py`, `dates.py` ni `sections.py`.
- **Tests**: `tests/test_state.py`, `tests/test_watcher.py`, `tests/test_cycle.py`, `tests/test_scrape.py` y `tests/test_state_atomic.py` (el corte entre `write_text` y `os.replace` sigue siendo el mismo camino; el nombre del temporal cambia). Hoy la suite está en **153 passed**.
- **Datos/estado**: sin migración y sin cambio de formato de los registros de `estado.json`; se agrega la clave reservada `__meta__` (sólo mientras hay un digest pendiente). Las entradas viejas sin `cierre_base` siguen adoptando la base sin alertar.
- **Operación**: la acción de infraestructura pendiente (volumen en `/data`) queda documentada en `docs/estado.md`; el log deja de ser ciego ante su ausencia.
- **Riesgo residual aceptado**: mientras el volumen no exista, cada deploy producirá un 🆕 legítimo desde el punto de vista del bot; lo que cambia es que el log lo explica.
- **Bug extra detectado (se reporta, no se arregla fuera de este change)**: `state.py:31` asigna a `_data` **lo que sea** que devuelva `json.loads`. Un archivo con `null`, `[]` o `"texto"` decodifica sin excepción y deja `_data` como `None`/`list`/`str`; `is_new` (`state.py:47`) revienta con `TypeError` y la corrida muere con código 1. El mismo camino de carga que este change vuelve explícito lo clasifica como `corrupto`, así que queda cubierto por el punto 1; se documenta acá para que no se pierda el hallazgo.
- **Changes archivados**: `2026-09-29-moodle-extraction`, `2026-10-01-date-change-watch` y las extensiones posteriores **no se tocan** (regla dura 4).
