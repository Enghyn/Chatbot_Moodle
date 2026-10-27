# Tasks

> Nada de esto se escribe a ojo: sin HTML real no hay RED posible (regla dura 5). Todo el HTML necesario **ya está descargado y verificado** en `archivos_web_scrap/`.

> **Nota de apply (2026-10-17)**: `archivos_web_scrap/` **no contiene ninguna página `mod/resource`** (todas son `page-mod-assign-view` o `page-course-view-onetopic`): no existe ningún `page-mod-resource-view` real entre los 7 HTML disponibles.

> **Decisión posterior (2026-10-27) — D4 retirada**: los `mod/resource` del curso de Programación son un **PDF** (`cm 1834`) y un **markdown** (`cm 1835`). Para un `mod/resource` de tipo archivo, `view.php` es solo una pantalla de descarga/redirección: **no hay cuerpo de página donde buscar fechas**. El supuesto que sostenía la cobertura de páginas es falso, así que se retira D4 completa (código, tests y spec) en vez de mantener código especulativo sin caso de uso ni fixture real. D1, D2, D3, D5 y D6 quedan intactas.

## 1. Fixtures reales (desde HTML ya descargado)

- [x] 1.1 Copiar `archivos_web_scrap/prog3_seccion42_práctica_Relaciones_y_Estado.html` → `tests/fixtures/prog3_seccion42_relaciones.html`. Verificar que contiene `li.activity-wrapper` con `id="module-1833" data-id="1833"` (línea ~5869 del original).
- [x] 1.2 Copiar `archivos_web_scrap/PROG3A26_ Entrega TP Libreria Backend _ CVT.html` → `tests/fixtures/assign_libreria_1833.html`. Verificar que su `div[data-region="activity-dates"]` expone `Apertura:` (15 oct 2026 00:00) y `Cierre:` (18 oct 2026 23:59).
- [x] 1.3 **Nombres con número de sección** (D5): el curso 14 tiene tres tabs "Práctica 💻" (FastAPI sec 31, SQLModel sec 36, Relaciones y Estado sec 42); guardar por título pisa archivos. Ningún fixture nuevo puede llamarse solo `tema_prog3_practica`.
- [x] 1.4 Registrar ambos en `tests/fixtures/manifest.json` (`curso`, `seccion`, `tiene_fecha`, `origen`) y **actualizar `EXPECTED` en `tests/test_fixtures_inventory.py`**, que asserta igualdad exacta de keys. Verificar con `pytest tests/test_fixtures_inventory.py` en verde.

## 2. Identidad de la actividad (D1)

- [x] 2.1 RED: en `tests/test_activities.py`, con el fixture `prog3_seccion42_relaciones.html`, afirmar que la actividad se registra con `id == "1833"` y **no** con el id del curso `14`.
- [x] 2.2 RED: con un `li.activity-wrapper` cuyo único anchor con `id=` es `course/view.php?id=14&section=40#module-1522`, afirmar que la actividad resultante no lleva `id="14"` (debe resolverse por la fuente 3, `#module-1522`, o descartarse). Verificar que ambos tests fallan con la implementación actual.
- [x] 2.3 GREEN: reordenar la resolución del cmid en `activities.py` según D1 (`data-id` / `id="module-N"` → `mod/*/view.php?id=` → ancla `#module-N` → descarte con motivo `sin_id`). Verificar los tests de 2.1/2.2 y toda la suite existente de `tests/test_activities.py` en verde.
- [x] 2.4 Cubrir el `li.activity-wrapper` sin ninguna fuente de id → se descarta y no aparece en la lista, con su propio motivo. Test propio en `tests/test_activities.py`.
- [x] 2.5 Assertar que `extract_activity_from_detail` no deriva el id de una URL `course/view.php` (o que, si lo hace, no puede colisionar con el id del curso). Test propio.

## 3. Descarte diagnosticable (D2)

- [x] 3.1 RED: en `tests/test_scrape.py`, con `caplog`, afirmar que una actividad descartada por falta de fecha emite un `warning` con `id`, `title`, `curso` y `sección`; y que el descarte por falta de id (`sin_id`) emite su propio motivo. Verificar que hoy no hay ningún log.
- [x] 3.2 GREEN: agregar el helper de descarte en `scrape.py` con los motivos `sin_fecha`, `sin_id`, `detalle_fallo` y usarlo en **cada** `continue` (incluido el de fallo del GET de sección y el de fallo del GET de detalle). Verificar en verde.
- [x] 3.3 RED/GREEN: cuando los descartes de una corrida superan el umbral (50), se emite el resumen agregado con conteo por motivo en lugar del detalle uno por uno. Test que genere muchos descartes.
- [x] 3.4 Test que asserte que el warning **no** contiene cookies, `MoodleSession`, `logintoken`, usuario ni password (regla dura 1 / RN-GLB-02).

## 4. Resumen de cierre de corrida (D3)

- [x] 4.1 RED: en `tests/test_scrape.py`, afirmar que al terminar `collect_candidates` se emite un `info` con `secciones=`, `actividades=`, `candidatas=`, `descartes_por_motivo=` y `duracion_s=`. Verificar que hoy no existe.
- [x] 4.2 GREEN: emitir el resumen al cierre. Verificar en verde.
- [x] 4.3 Justificar en el docstring de `collect_candidates` que el costo de la corrida (~93 s medidos en producción para 3 cursos × ~44 secciones) queda observable con este resumen.

## 5. Cobertura de páginas `mod/resource` (D4) — **RETIRADA**

> Todas las tasks de esta sección quedan **eliminado por decisión — no hay caso de uso real: los `mod/resource` del curso son PDF/MD, no páginas**. El código y los tests de D4 se borraron; `mod/resource` vuelve a quedar fuera del alcance y su descarte sigue siendo diagnosticable por D2 (`sin_fecha`).

- [x] 5.1 ~~RED: una página `mod/resource` con fecha en su contenido aparece entre las candidatas~~ → **eliminado por decisión — no hay caso de uso real: los `mod/resource` del curso son PDF/MD, no páginas**. Nunca hubo fixture real (`archivos_web_scrap/` no tiene ningún `page-mod-resource-view`).
- [x] 5.2 ~~GREEN: fallback de contenido opt-in (`parse_page_dates`)~~ → **eliminado por decisión**. La función `parse_page_dates` se borró de `dates.py`.
- [x] 5.3 ~~RED/GREEN: página sin fecha en ningún nivel se descarta con warning~~ → **eliminado por decisión**. El caso "sin fecha" ya lo cubren los tests de D2 (3 assigns reales sin `activity-dates`).
- [x] 5.4 ~~RED/GREEN: fecha en prosa sin alias no genera candidata~~ → **eliminado por decisión**. Sin fallback de contenido no aplica.
- [x] 5.5 Confirmar con `assign_libreria_1833.html` que el camino de `mod/assign` **no cambia**: `parse_activity_dates` sigue devolviendo `{start: 2026-10-15 00:00, due: 2026-10-18 23:59}`. Test de regresión conservado en `tests/test_dates.py::test_regresion_cm_1833_assign_real` (sin referencia al fallback de páginas).
- [x] 5.6 Confirmar que `tests/test_nodate.py` sigue en verde (los 3 assigns sin fecha conocidos continúan descartándose, ahora con warning). Verificado tras la retirada de D4.

## 6. Documentación y registro

- [x] 6.1 Actualizar `knowledge-base/05_reglas_de_negocio.md`: RN-EXT-02 (descarte registrado en lugar de silencioso, default NO-notificar intacto) y RN-EXT-06 (identidad de la actividad por cmid). RN-EXT-04 vuelve a quedar sin cobertura de `mod/resource` tras la retirada de D4.
- [x] 6.2 Actualizar `docs/filtros.md` con la nota de que el descarte por falta de fecha ahora deja `warning` en el log y que existe un resumen de cierre de corrida.
- [x] 6.3 Registrar el change en `CHANGES.md`.
- [x] 6.4 Verificar que `CHANGES.md` y la KB no contradicen `openspec/specs/moodle-extraction/spec.md` (el spec principal se actualiza al archivar, no antes).

## 7. Verificación de integración

- [x] 7.1 `pytest` completo en verde y sin tests saltados. → **142 passed** (153 antes de retirar D4: se borraron 11 tests de páginas `mod/resource`, 7 en `test_dates.py` y 4 en `test_scrape.py`; el test de regresión de `mod/assign` con `assign_libreria_1833.html` se conservó).
- [x] 7.2 `git status`: confirmar que **no** hay modificaciones bajo `openspec/changes/archive/` (regla dura 4). → limpio.
- [x] 7.3 Confirmar por **lectura de código** que el título del mensaje sigue siendo el de Moodle verbatim — no se tocó `formatting.py` ni `grouping.py` (decisión explícita del usuario). → `git diff --stat` vacío para `formatting.py`, `grouping.py`, `filters.py`, `comision.py`, `sender.py`, `cycle.py`.
- [ ] 7.4 Verificación en vivo **sin `--dry-run` en producción** (D6). **PENDIENTE — requiere acceso al VPS.** Localmente se verificó la observabilidad con fixtures reales (`corrida: secciones=2 actividades=4 candidatas=1 descartes_por_motivo={'sin_fecha': 3, 'sin_id': 2} duracion_s=0.5`), sin tocar `estado.json` ni enviar nada.

---

## Pendiente para cerrar el change

- [ ] **7.4**: verificación en vivo leyendo los logs de la corrida real en EasyPanel (sin `--dry-run`: `cycle.py:56` marca estado igual que un envío real). La retirada de D4 no deja pendientes de fixture: ya no hay ninguna página `mod/resource` en el alcance.