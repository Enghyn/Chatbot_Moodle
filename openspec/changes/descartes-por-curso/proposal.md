# Proposal

## Why

El mecanismo de diagnóstico del scraping —introducido en el change archivado `2026-10-28-visibilidad-y-diagnostico-actividades`— **falla justo en el curso para el que fue construido**. La corrida real del 2026-10-27 20:00 lo dejó documentado:

```
INFO corrida: secciones=91 actividades=163 candidatas=15
  descartes_por_motivo={'sin_fecha': 148, 'sin_id': 113} duracion_s=98.6
```

El detalle por ítem se cortó en 50 líneas y esas 50 se las comieron los dos primeros cursos recorridos (Inglés `743` y BD2 `723`). La última línea de detalle fue a las 20:00:27, en la sección 7 de BD2; de ahí al cierre (20:01:48) hay silencio total. **El curso de Programación (`14`) no emitió ni una línea de detalle**, y es exactamente el curso donde apareció el problema original (la entrega que no se encontraba).

La causa está en `src/bot_moodle/scrape.py`: `_RegistroDescartes` mantiene **un solo contador global** y el umbral de 50 es global, así que el primer curso agota el presupuesto de detalle de toda la corrida y los siguientes quedan ciegos:

```python
def registrar(self, motivo, *, act=None, course_id="", ...):
    self.conteo[motivo] += 1
    if self.total > self.umbral:   # ← global: gana el que llega primero
        return
```

Un log que promete "todo descarte es diagnosticable" y luego omite un curso entero no es diagnóstico: es una omisión silenciosa con formato de cobertura parcial.

## What Changes

- **El techo de 50 descartes pasa a ser por curso**: cada curso recibe su propio presupuesto de líneas de detalle, así el último curso de la corrida emite las suyas aunque los anteriores hayan agotado su cuota. Una corrida con 3 cursos puede emitir hasta ~150 líneas de detalle en vez de 50. Costo aceptado y explícito: el log crece, pero deja de mentir por omisión.
- **La línea de cierre suma `descartes_por_curso`**, con el conteo de descartes por curso, en el mismo estilo de `dict` ordenado que `descartes_por_motivo` — para ver el desbalance de un vistazo sin contar líneas a mano: `descartes_por_curso={'14': 11, '723': 130, '743': 120}`.
- **`descartes_detalle_omitido` se conserva**, recalculado como la suma de los excedentes por curso: `Σ max(0, descartes_curso − umbral)`.
- **`descartes_por_motivo`, los motivos y el flujo de notificación no cambian.** Tampoco el nombre ni la presentación del mensaje de WhatsApp.

## Capabilities

### New Capabilities

_(ninguna)_

### Modified Capabilities

- `moodle-extraction`: *Solo entregas con fecha parseable* — el techo de ruido del detalle pasa a aplicarse por curso (no por corrida) y el resumen de cierre incorpora el desglose `descartes_por_curso` además del `descartes_por_motivo`. La obligación de registrar cada descarte y el default NO-notificar no cambian.

## Impact

- **Código**: sólo `src/bot_moodle/scrape.py` (`_RegistroDescartes`: contador por curso y umbral por curso; `_resumen_cierre`: campo nuevo y recálculo del omitido). Sin cambios en `activities.py`, `dates.py`, `filters.py`, `formatting.py`, `grouping.py`, `sender.py` ni `cycle.py`.
- **Tests**: `tests/test_scrape.py` (nuevos casos con `caplog` sobre multi-curso, orden determinista del dict y conteo de `sin_sesion`; el caso existente de 60 descartes en un solo curso sigue verde porque un curso único con 60 descartes sigue cortando en 50). Sin fixtures nuevos: el change es de logging y se testea con el HTML mínimo que ya usan esos tests.
- **Docs**: `docs/filtros.md` (documenta hoy el umbral de 50 como global) y `CHANGES.md` (entrada del change). La knowledge base **no se toca**: RN-EXT-02 describe el contrato de descarte registrado y el resumen por motivo/duración, no el valor ni el alcance del techo, que es una decisión operativa interna de logging.
- **Datos/estado**: sin cambios en `estado.json` ni migración. El único efecto persistido son líneas de log (más largas, sin secretos).
- **Riesgo operativo**: sube el volumen de log por corrida (hasta ~3× el detalle actual en una corrida de 3 cursos con muchos descartes). Se acota con el mismo techo, ahora por curso; no hay agregación por campus ni por sección (evita diseño especulativo).
- **Changes archivados**: no se tocan (regla dura 4). La corrección del alcance del umbral entra como delta nuevo.

## Non-Goals

- **NO** cambia la semántica de qué se descarta ni los motivos (`sin_fecha`, `sin_id`, `detalle_fallo`, `seccion_fallo`, `sin_sesion`).
- **NO** se emite un warning por curso que se queda sin presupuesto: eso reintroduciría el flood que el techo evita.
- **NO** se toca el nombre ni la presentación del mensaje de WhatsApp.
- **NO** se toca `activities.py` (identidad de actividad), `dates.py`, `filters.py`, `formatting.py`, `grouping.py`, `sender.py` ni `cycle.py`.
- **NO** se reabre ni se modifica el change archivado.
- **NO** se agrega agregación por campus ni por sección: sólo por curso.
