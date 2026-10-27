# Design

## Context

El change se propone sobre un diagnóstico hecho **con ejecución real del código contra el HTML real** (no sobre hipótesis). Ver `proposal.md` para el resultado: el aviso faltante era un falso positivo y el bot notificó `cm 1833` correctamente en la corrida del 16/10 20:00.

Lo que queda en pie, verificado:

- `sections.py:90-130` (`enumerate_sections`) recorre todas las secciones del índice (44 en el curso 14). No hay allowlist de módulos; la única lista hardcodeada es la de cursos (`main.py:27-31`). **El scope no es el problema.**
- `activities.py:9` usa `_ID_RE = re.compile(r"[?&]id=(\d+)")`, que no distingue el `id` del cm del `id` del curso y toma el **primer** anchor que matchea dentro de `li.activity-wrapper`. Con anchors `course/view.php?id=14&section=40#module-XXXX` registra una actividad espuria con `id="14"`.
- El HTML real ya expone la fuente autoritativa: `archivos_web_scrap/prog3_seccion42_práctica_Relaciones_y_Estado.html:5869` →
  `<li class="activity activity-wrapper assign modtype_assign hasinfo" id="module-1833" data-for="cmitem" data-id="1833" data-indexed="true">`.
- `dates.py:44-63` **funciona**: sobre el detail de `cm 1833` (`archivos_web_scrap/PROG3A26_ Entrega TP Libreria Backend _ CVT.html`) devuelve `{start: 2026-10-15 00:00, due: 2026-10-18 23:59}` desde `div[data-region="activity-dates"]` con alias `Apertura:` / `Cierre:`. **No se toca el parseo de formatos.**
- `scrape.py:44-52` descarta con `continue` sin log cuando `parsed["due"] is None`, y tampoco loguea qué encontró. En producción EasyPanel solo queda `C1: sesion valida` / `C2: sesion valida` / `Job "..." executed successfully`.
- La sección `42` contiene **un solo** `li.activity-wrapper` (el assign `1833`). los `mod/resource` `1834` ("PLANTILLA PROMPTS PARCIAL 1") y `1835` ("Consigna Parcial 1") que existen en esa unidad son **un PDF y un markdown**: no son páginas de contenido, así que no hay cuerpo donde buscar fechas y quedan fuera del alcance (ver D4 retirada).

Restricciones: los changes archivados no se tocan; TDD con fixtures HTML reales (regla dura 5); nunca secretos en logs (regla dura 1 / RN-GLB-02); default NO-notificar (RN-GLB-01); sin dependencias nuevas.

## Goals / Non-Goals

**Goals:**
- Que ninguna entrega falte sin dejar rastro: todo descarte queda registrado y diagnosticable, y cada corrida deja un resumen con encontrados / candidatas / descartes / duración.
- Que el identificador de actividad sea siempre el cmid real.

**Non-Goals:**
- **No** se toca el nombre ni la presentación del mensaje: el título de Moodle se muestra verbatim (decisión consciente del usuario).
- **No** se amplían los formatos de fecha ni se modifica el default NO-notificar.
- No se agregan otros módulos (`mod/url`, `mod/forum`, `mod/book`, `mod/quiz`): ampliarían scope sin evidencia de que hoy fallen.
- No se cambian filtros de comisión, ventana temporal de 14 días, formato de mensajes ni envío por Evolution API.
- No se migra `estado.json` ni se cambia su formato.
- No se instrumenta el scheduler ni se toca `main.py`/`scheduler.py`.

## Decisions

### D1 — Resolver el cmid por prioridad de fuentes del DOM, no por "primer anchor que matchea"
Orden en `extract_activities`:
1. `data-id` del propio `li.activity-wrapper`, o `id="module-<N>"`.
2. `mod/*/view.php?id=<N>` en un anchor del contenedor.
3. Ancla `course/view.php?...#module-<N>` → se toma `<N>` (es el módulo al que apunta el ancla).
4. Sin fuente 1–3 → se descarta la actividad con motivo `sin_id` y warning.

**Por qué**: `data-id` / `id="module-N"` es autoritativo (lo emite Moodle para el cm) y no depende del texto de la URL. El fallback por ancla conserva la cobertura cuando el `li` no trae `data-id`.

**Alternativa descartada**: regex negativa que solo acepte `mod/`. Es simple, pero deja fuera los anchors `#module-N` y obliga a reinventar el parseo por fragmento. Con el orden 1→4 el comportamiento queda definido sin regex negativo frágil.

**Verificación disponible**: el fixture real de la sección `42` tiene `data-id="1833"` y `id="module-1833"`; el anchor del courseindex apunta a `mod/resource/view.php?id=<cmid>` (nunca a `course/view.php`), así que la fuente 1 resuelve sin ambigüedad.

### D2 — Descartes diagnosticables: un warning por actividad, con techo de ruido y resumen agregado
Helper único en `scrape.py` (p. ej. `_descarte(act, sec, motivo)`) que emite **un** `warning` por actividad descartada con `id`, `title`, `modtype`, `course_id`, `section index` y `motivo` (`sin_fecha`, `sin_id`, `detalle_fallo`). Se usa en cada `continue`. Cuando los descartes de una corrida superan un umbral (50), el detalle uno por uno se sustituye por un resumen con el conteo por motivo.

**Por qué**: el descarte silencioso es la causa raíz que hizo esta investigación costosa — diagnosticar requirió bajar HTML a mano, correr el código local, traer el log del VPS y leer `estado.json` a pulso. Hacerlo diagnosticable es en sí mismo el entregable.

**Por qué el techo**: hoy hay al menos 3 assigns conocidos sin fecha (`assign_bd2_tp_u4_56812`, `assign_met_u6_1581`, `assign_fastapi_1384`). Sin agregación, el log de cada corrida quedaría inundado de ruido conocido y volvería a ser inútil para el caso interesante.

**Por qué `warning` y no `error`**: no es un error; el sistema está comportándose según RN-EXT-02, solo opaco.

**Restricción dura**: el log nunca incluye cookies, `MoodleSession`, `logintoken`, usuario ni password (regla dura 1). Solo ids, títulos, `modtype`, curso, sección y motivo — el mismo conjunto de datos que ya viaja en el mensaje (RN-EXT-05 verbatim).

### D3 — Resumen de cierre de corrida, con duración explícita
`collect_candidates` cierra con un único `info` por corrida: `secciones=`, `actividades=`, `candidatas=`, `descartes_por_motivo=`, `duracion_s=`. La duración se expone porque **cada corrida actual tarda ~93 s** para 3 cursos × ~44 secciones: es un margen ajustado y hoy no hay forma de saber si una corrida se está acercando al timeout o si se está degradando el número de actividades encontradas.

**Por qué**: sin este resumen, ni un descarte ni un alza de duración son detectables en producción. Es la mitad "preventiva" del mismo hallazgo que D2 cubre "reactiva".

### D4 — **RETIRADA**: cobertura de páginas `mod/resource`
Se implementó un fallback de contenido (`parse_page_dates` en `dates.py`, rama `modtype == "resource"` en `scrape.py`) bajo el supuesto de que existían páginas de contenido con fechas en el cuerpo. **El supuesto es falso y está verificado**: los `mod/resource` del curso de Programación son un **PDF** (`cm 1834`) y un **markdown** (`cm 1835`); cuando un `mod/resource` es un archivo, `view.php` es solo una pantalla de descarga/redirección, sin contenido donde buscar fechas, y no hay ningún `page-mod-resource-view` real entre los HTML disponibles.

**Decisión (2026-10-27)**: retirar la cobertura completa —código, tests y spec— en lugar de mantener código especulativo sin caso de uso ni fixture real. `mod/resource` vuelve a quedar fuera del alcance; sus actividades se descartan con el motivo `sin_fecha` (RN-EXT-02), igual que antes y ahora **visible en el log** gracias a D2. La numeración D5/D6 se conserva para no romper referencias.

### D5 — Los fixtures nuevos llevan el número de sección en el nombre
`tests/fixtures/prog3_seccion42_relaciones.html` y `tests/fixtures/assign_libreria_1833.html`. En el curso 14 hay **tres** tabs llamados "Práctica 💻" (FastAPI sec 31, SQLModel sec 36, Relaciones y Estado sec 42); guardar por título de tab pisa archivos. Además `tests/test_fixtures_inventory.py` asserta **igualdad exacta de keys** entre `EXPECTED` y `manifest.json`: agregar fixtures rompe el test y su actualización es una tarea explícita, no un efecto colateral.

### D6 — La verificación en vivo no usa `--dry-run`
`cycle.py:56` tiene `if sent or dry_run:` y llama `store.mark_seen(...)`: **un `--dry-run` marca las candidatas como vistas igual que un envío real**, así que en producción el vigía posterior puede no avisar. La verificación en vivo de este change se hace por logs de la corrida real (que es justamente lo que D2/D3 vuelven observable) o, si se necesita `--dry-run`, sobre un `estado.json` de copia y documentando el riesgo.

## Risks / Trade-offs

- **[Más requests por corrida]** → 1 GET por actividad con link, como antes: la retirada de D4 elimina el GET extra que se hacía por cada página `mod/resource` encontrada. El resumen de D3 deja el costo visible.
- **[El warning nuevo puede delatar cuasi-identificadores en títulos]** → es el mismo dato que ya viaja en el mensaje de WhatsApp (RN-EXT-05 verbatim); no se agrega ningún dato nuevo.
- **[Colisión de clave de estado]** → no aplica: los cmid de Moodle son globales; el bug era usar el id de *curso*, corregido en D1. La clave espuria `cmid=14` no llega hoy a persistirse (el descarte por fecha la precede), por eso no hay migración.
- **[El logging nuevo escribe en producción]** → solo ids, títulos, `modtype`, curso, sección, motivo y duración. Sin secretos. Con el techo de D2 el volumen por corrida es acotado.

## Migration Plan

1. Implementar sobre la rama de trabajo; `pytest` en verde antes de cualquier deploy.
2. No hay migración de datos.
3. Rollback: revertir el commit. El único efecto persistido nuevo son entradas de log.

## Open Questions

- _(cerradas)_ Las dos preguntas originales eran sobre las páginas `mod/resource` (`cm 1834` / `cm 1835`). Se verificó que son un PDF y un markdown, no páginas de contenido, así que se retiró D4 y ambas dejan de aplicar: no hay fallback de contenido ni riesgo de duplicar la fecha entre página y assign.