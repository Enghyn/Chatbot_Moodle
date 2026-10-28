# Proposal

## Why

El aviso reportado como faltante —la entrega del módulo nuevo **"Relaciones y Estado"** (Programación 3, `course_id=14`, sección `42` "Práctica 💻")— **no fue un bug**. El diagnóstico con ejecución real del código contra el HTML real lo cerró como falso positivo:

- `enumerate_sections` devuelve 44 secciones, la `42` incluida → el scope se recorre.
- `extract_activities` sobre el HTML real de la sección `42` devuelve `{id: '1833', modtype: 'assign', title: 'Entrega TP Libreria Backend Tarea', url: 'mod/assign/view.php?id=1833'}` → id correcto, no confunde curso con actividad.
- `parse_activity_dates` sobre el detail de `cm 1833` devuelve `{start: 2026-10-15 00:00, due: 2026-10-18 23:59}` → el parser lee el `div[data-region="activity-dates"]` con alias `Apertura:` / `Cierre:` sin problema.
- `should_include(...)` → `True`; `filter_window(14 días)` → entra; urgente (≤7 días) → sí.
- **La corrida del 16/10 20:00 notificó la entrega correctamente.** `/data/estado.json` lo confirma: hasta esa corrida solo había 2 entradas en toda la historia (cmid `1309` y `1766`, ambas `visto: 2026-10-05T09:00:17`); el `1833` no estaba hasta que la corrida lo registró.

Causa real del "no lo vi": la actividad **no era visible para el bot** hasta después de la corrida del 16/10 08:00. La fecha `Apertura: 15 oct 00:00` es la **ventana de entrega configurada por el docente**, no la de publicación. Los cmid del módulo subieron de `1522/1531/1532` a `1833/1834/1835` (+300), lo que confirma que se crearon muchas actividades después de los HTML descargados a mano. Además el usuario buscó por "Relaciones y Estado" mientras Moodle la titula "Entrega TP Libreria Backend".

De ese diagnóstico se descartan explícitamente las hipótesis con las que se propuso originalmente este change:

- ❌ **"el assign se descarta por `activity-dates` ausente o por un formato de fecha no parseable"** → **refutada**. El HTML tiene `activity-dates` y el parser lo lee. **Sale del alcance**: no se toca `dates.py` ni se amplían formatos de fecha.
- ✅ **"`_ID_RE` matchea el id del curso"** → **se mantiene**. Confirmado en `activities.py:9`: `_ID_RE = re.compile(r"[?&]id=(\d+)")` matchea `id=14` (el id del **curso**) en anchors `course/view.php?id=14&section=40#module-XXXX`, registrando una actividad espuria con `id="14"` y contaminando la clave de estado de `estado.json`.
- ❌ **"`mod/resource` (páginas) fuera del scope"** → **retirada (2026-10-27)**. El supuesto era que existían páginas de contenido con fechas en el cuerpo. Es falso: los `mod/resource` del curso de Programación son un **PDF** (`cm 1834`) y un **markdown** (`cm 1835`). Cuando el `mod/resource` es un archivo, `view.php` es solo una pantalla de descarga/redirección, sin cuerpo donde buscar fechas; no hay ningún `page-mod-resource-view` real en los HTML disponibles. Mantener un fallback de contenido sería código especulativo sin caso de uso ni fixture real, así que sale del alcance. El descarte de esos `mod/resource` queda igual de visible que el de cualquier actividad sin fecha (D2, motivo `sin_fecha`).
- 🆕 **Causa raíz nueva, y fue la más costosa: el log de producción es ciego.** En EasyPanel cada corrida registra solo `C1: sesion valida`, `C2: sesion valida`, `Job "..." executed successfully`. No dice qué actividades se encontraron, cuáles se descartaron ni por qué. El descarte es **totalmente silencioso** (`scrape.py:51-52` → `continue` sin log). Diagnosticar este caso requirió descargar HTML a mano, correr el código localmente, traer el log del VPS y leer `/data/estado.json` a pulso. Dato de entorno asociado: **cada corrida dura ~93 s** para 3 cursos × ~44 secciones, un margen ajustado y sin logging que lo haga observable.

## What Changes

- **Agregar logging diagnosticable de descartes**: un `warning` por actividad descartada con `id`, `title`, `modtype`, `course_id`, `section index` y `motivo` (`sin_fecha`, `sin_id`, `detalle_fallo`), más un resumen agregado por conteo de motivos cuando los descartes de una corrida superen un umbral (hoy hay al menos 3 assigns conocidos sin fecha que inundarían el log con detalle uno por uno). Nunca cookies, tokens, `logintoken`, usuario ni password (regla dura 1 / RN-GLB-02). Se agrega además un resumen de cierre de corrida (actividades encontradas, candidatas, descartes por motivo, duración) que hace observable el costo de los ~93 s.
- **Corregir la identidad de actividad** en `activities.py`: el cmid sale de la fuente autoritativa del DOM — `data-id` / `id="module-<N>"` del propio `li.activity-wrapper`, que el HTML real ya trae (línea 5869 del fixture de la sección `42`: `id="module-1833" data-id="1833"`) — y nunca del parámetro `id` de `course/view.php`, que es el del curso.
- **NO tocar** el nombre ni la presentación del mensaje: el bot sigue mostrando el título de Moodle verbatim. Es una decisión consciente del usuario — el aviso llegó igual; el "no lo vi" fue por buscar un texto que Moodle no usa en el título.
- **Actualizar** `knowledge-base/05_reglas_de_negocio.md` (RN-EXT-02 y RN-EXT-06) y `docs/filtros.md` para reflejar el nuevo contrato de descarte registrado y la identidad de actividad por cmid.
- **Agregar cobertura con fixtures reales** ya verificados: vista de la sección `42` del curso 14 (`archivos_web_scrap/prog3_seccion42_práctica_Relaciones_y_Estado.html`) y detail del `cm 1833` (`archivos_web_scrap/PROG3A26_ Entrega TP Libreria Backend _ CVT.html`). Los fixtures nuevos llevan **el número de sección en el nombre** (`prog3_seccion42_relaciones.html`), porque en el curso 14 hay tres tabs llamados "Práctica 💻" (FastAPI sec 31, SQLModel sec 36, Relaciones y Estado sec 42) y guardar por título pisa archivos.

## Capabilities

### New Capabilities

_(ninguna)_

### Modified Capabilities

- `moodle-extraction`: *Solo entregas con fecha parseable* (RN-EXT-02 deja de descartar en silencio: exige descarte registrado y diagnosticable, sin cambiar el default NO-notificar ni los formatos de fecha ya soportados) y *Identidad de la actividad por módulo de curso* (nueva: el cmid nunca sale del `id` del curso).

## Impact

- **Código**: `src/bot_moodle/activities.py` (resolución de cmid por `data-id` / `id="module-N"` y descarte con motivo `sin_id`), `src/bot_moodle/scrape.py` (helper de descarte + resumen de corrida). `src/bot_moodle/dates.py` **sin cambios netos** (la retirada de D4 borra el fallback de contenido para páginas: los regex y formatos existentes nunca se tocaron). Sin cambios en `comision.py`, `filters.py`, `formatting.py`, `sender.py`.
- **Tests/fixtures**: `tests/fixtures/prog3_seccion42_relaciones.html` y `tests/fixtures/assign_libreria_1833.html` (nuevos, desde `archivos_web_scrap/`), `tests/fixtures/manifest.json` y `tests/test_fixtures_inventory.py` (el inventario asserta **igualdad exacta de keys** contra `EXPECTED`: agregar fixtures rompe el test y hay que actualizarlo — tarea explícita), `tests/test_activities.py`, `tests/test_scrape.py`, `tests/test_dates.py`.
- **Docs**: `knowledge-base/05_reglas_de_negocio.md`, `docs/filtros.md`, `CHANGES.md`.
- **Datos/estado**: sin cambios de formato en `estado.json` ni migración. El fix del cmid evita la clave espuria `cmid=<id_curso>`; hoy esa clave no llega a persistirse porque el descarte por fecha la precede.
- **Riesgo operativo documentado**: `cycle.py:56` (`if sent or dry_run:`) marca estado igual que un envío real, así que un `--dry-run` en producción deja las candidatas como vistas y el vigía real posterior puede no avisar. Cualquier verificación en vivo de este change debe evitar `--dry-run` o documentar el riesgo.
- **Sin impacto** en autenticación, filtros de comisión, ventana temporal, formato de mensajes ni envío por Evolution API.
- **Changes archivados**: `2026-09-29-moodle-extraction` y `2026-10-01-date-change-watch` **no se tocan** (regla dura 4); todo entra como delta.