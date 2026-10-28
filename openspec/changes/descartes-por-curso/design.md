# Design

## Context

Ver `proposal.md` para la motivación. El estado actual relevante es concreto y está en un solo archivo, `src/bot_moodle/scrape.py`:

- `_RegistroDescartes` acumula `self.conteo: Counter[str]` **por motivo** y corta el detalle con `if self.total > self.umbral`, donde `total` es la suma de todos los motivos de toda la corrida. Un único contador global ⇒ el primer curso consumido se lleva el presupuesto.
- `registrar()` ya recibe `course_id` en **todos** los llamados (`sin_sesion`, `seccion_fallo`, `sin_id` vía el closure `_sin_id`, `detalle_fallo`, `sin_fecha`), así que la información necesaria para particionar ya está en la firma: no hay que tocar `collect_candidates` para pasarla.
- `_resumen_cierre()` calcula `omitido = max(0, descartes.total - descartes.umbral)` y arma **una** línea `info` con f-string. Esa forma (una línea, `INFO`, interpolada) es una restricción aprendida en producción: la versión con argumentos diferidos imprimió una tupla cruda y se corrigió en el commit `4e1f5c8`. El test `test_sobre_el_umbral_la_duracion_del_cierre_es_parseable_como_float` la sostiene.
- Tests existentes que fijan el contrato actual: `test_mas_de_50_descartes_cortan_el_detalle_en_50_y_el_cierre_refleja_el_total_real` (60 descartes en **un** curso), `test_sobre_el_umbral_el_cierre_es_info_totalmente_interpolado_con_el_truncamiento` (`descartes_detalle_omitido=10` con 60 descartes), `test_el_warning_de_descarte_no_expone_secretos`, `test_bajo_el_umbral_el_cierre_no_lleva_el_campo_de_truncamiento`. Los cuatro deben seguir verdes: un curso único con 60 descartes sigue cortando en 50 y omitiendo 10.
- Restricciones: regla dura 1 (nunca secretos en logs), regla dura 4 (no tocar el change archivado), regla dura 5 (TDD: RED antes de GREEN), regla dura 7 (suite en verde). Sin dependencias nuevas.

## Goals / Non-Goals

**Goals (de diseño):**

- Que el presupuesto de detalle de un curso no dependa del orden de recorrido ni del volumen de descartes de los otros cursos.
- Que el desbalance se lea de un vistazo en el cierre, sin contar líneas ni cruzar logs.
- Que el log de una corrida sea **reproducible**: mismo conjunto de descartes ⇒ misma línea de cierre, byte a byte.
- Cero cambios en la firma pública de `collect_candidates`, en el flujo de notificación y en el formato de `estado.json`.

**Non-Goals (de diseño):**

- No se rediseña `_RegistroDescartes` como subsistema de métricas ni se persiste nada en disco.
- No se agrega estructura por campus ni por sección (ver D1).
- No se unifica `sin_sesion` con el `logger.warning("%s: sin sesion, se omite curso %s")` que ya existe en `collect_candidates`: son dos líneas distintas y este change no cambia qué se loguea, sólo cómo se cuenta.

## Decisions

### D1 — Techo por curso, no por corrida

`_RegistroDescartes` pasa a tener, además del conteo por motivo, un conteo por curso, y el corte del detalle se evalúa contra el contador **del curso del descarte**:

```python
self.por_curso[clave] += 1
if self.por_curso[clave] > self.umbral:
    return                      # silencio para ESE curso, no para la corrida
```

**Por qué**: el umbral existe para que el ruido conocido no tape el caso interesante. Con un contador global, el ruido conocido de un curso *es* el que tapa el caso interesante de otro — el mecanismo se autodestruye. Con un techo por curso, la garantía útil ("el curso que me importa siempre deja rastro") se cumple sin depender del orden de `targets`.

**Costo aceptado y documentado**: una corrida puede pasar de 50 a `50 × n_cursos` líneas de detalle (~150 en la corrida real de 3 cursos). El log crece; el cierre sigue siendo una sola línea y el ruido por curso sigue acotado. Este trade-off ya fue decidido por el usuario y no se reabre.

**Alternativas descartadas:**

- **Techo global (status quo)**: es el bug. La corrida del 2026-10-27 lo probó: el curso `14` quedó con cero líneas de detalle y es justo el que motivó todo el trabajo previo.
- **Sólo desglose por curso, sin techo**: el desglose arregla la *lectura* del cierre pero no la *cobertura* del detalle. Con 148 `sin_fecha` y 113 `sin_id` el log pasaría de 50 a 261 líneas por corrida; el caso interesante seguiría enterrado, ahora en un log más largo.
- **Techo más alto (p. ej. 200) manteniendo el contador global**: mueve el problema sin resolverlo (con 4 cursos y una corrida ruidosa vuelve a aparecer) y hace el umbral dependiente de cuántos cursos haya en el momento.
- **Agregación por campus o por sección**: el desbalance diagnosticado es por curso (un curso entero ciego). Campus agrupa dos cursos distintos entre sí y sección fragmenta el presupuesto en 91 buckets (umbral efectivo ~91×50): complejidad y ruido sin caso de uso.

### D2 — Clave canónica de curso: `str(course_id)` o `'?'`

`course_id` viaja como `Any` y puede llegar `None` o `""` (`registrar` lo declara `course_id: Any = ""`; `_sin_id` lo toma de `t.get("course_id")`, que puede faltar). La clave se normaliza en un único helper:

```python
def _clave_curso(course_id) -> str:
    return str(course_id) if course_id not in (None, "") else "?"
```

**Por qué `'?'` y no `''`**: `''` se imprime como `{'': 3}` y es fácil de confundir con un artefacto de formato o con una clave vacía legítima; `'?'` se lee como "curso desconocido" en el log y en un assert. **Por qué no inventar un curso**: la regla dura 2 (nunca inventar datos ante dato ausente) aplica igual al log; una clave sentinel explícita dice la verdad (no sé de qué curso es) sin fabricar un id que después alguien pueda tomar por real. La clave queda documentada en `docs/filtros.md` y anclada en el scenario *Descarte sin curso identificable*.

Nota: en la práctica hoy todos los targets traen `course_id` (`main.py` lo exige), así que `'?'` es una red de seguridad, no el camino normal.

### D3 — `total` sigue siendo global; el truncamiento se calcula por excedentes

- `total` **se mantiene** como propiedad global (`sum(self.conteo.values())`), porque sigue siendo el número que interesa para verificar que el conteo por motivo cuadra con el conteo por curso, y porque hay asserts de test que lo usan como "total real de descartes". Lo que cambia es que **deja de gobernar el corte**.
- `descartes_detalle_omitido` deja de ser `total - umbral` y pasa a ser `Σ max(0, n_curso - umbral)` calculado sobre `por_curso` (propiedad nueva, p. ej. `excedente`). Ambas fórmulas coinciden con un solo curso (por eso los tests existentes de 60 descartes siguen verdes: 60−50 = 10) y difieren —correctamente— con varios.
- Invariante que conviene dejar como assert en test: `sum(por_curso.values()) == total`.

**Por qué no derivar el omitido de `total` y de las líneas efectivamente emitidas**: sería equivalente pero introduce un tercer contador que puede desincronizarse; el excedente por curso es la definición directa y auditable del contrato del spec.

### D4 — Orden determinista de `descartes_por_curso`

`resumen_por_curso()` devuelve `str(dict(sorted(self.por_curso.items())))` — mismo criterio que `resumen_texto()` ya usa para los motivos. Los ids de curso son strings (`'14'`, `'723'`, `'743'`), así que `sorted` es orden lexicográfico: `14 < 723 < 743` por casualidad de los largos, pero el contrato es "ordenado y estable", no "ordenado numéricamente". Documentarlo evita que alguien "arregle" el orden con un `key=int` que rompería con la clave `'?'`.

**Por qué**: el orden de inserción depende del recorrido de `targets` y del orden de los descartes dentro de cada curso; un dict en orden de inserción hace que dos corridas equivalentes produzcan líneas distintas, lo que rompe diffs de log, asserts de test y cualquier comparación entre corridas. `sorted` es más barato que garantizar el orden aguas arriba.

### D5 — `sin_sesion` cuenta en su curso

`collect_candidates` llama `descartes.registrar("sin_sesion", course_id=t.get("course_id"))` cuando no hay sesión para el campus. Ese descarte **sí entra** en `por_curso[clave del target]`: si un campus entero no tiene sesión, ese curso no se recorrió y el cierre debe mostrar ese hueco en el desglose, no esconderlo. Es el caso más grave de ceguera y el que más merece una clave propia en `descartes_por_curso`.

El comportamiento lateral no cambia: el `logger.warning("%s: sin sesion, se omite curso %s", ...)` que ya existe sigue ahí (una línea por campus caído), y `registrar("sin_sesion")` sigue emitiendo su propia línea de detalle si el curso está bajo el techo. No hay deduplicación ni se agrega warning nuevo por curso agotado (non-goal del proposal).

### D6 — Forma exacta de la línea de cierre

Un único `logger.info`, f-string, campos en este orden:

```
corrida: secciones=91 actividades=163 candidatas=15
  descartes_por_motivo={'sin_fecha': 148, 'sin_id': 113}
  descartes_por_curso={'14': 11, '723': 130, '743': 120}
  duracion_s=98.6
  [descartes_detalle_omitido=15]     ← sólo si > 0
```

(en la implementación, una sola línea; acá se muestra partida por ancho)

- `descartes_por_curso` va **después** de `descartes_por_motivo` (motivo primero: es el contrato previo; curso después: es el desglose nuevo) y **antes** de `duracion_s`, para no desplazar el campo que los tests parsean con `split("duracion_s=")`.
- `descartes_detalle_omitido` se sigue **agregando al final y sólo si > 0**, así el caso sin truncamiento no cambia ni una coma (los tests `test_bajo_el_umbral_el_cierre_no_lleva_el_campo_de_truncamiento` y `test_una_corrida_con_candidatas_no_emite_warning_de_resumen_agregado` dependen de eso).
- `descartes_por_curso` se emite **siempre**, también cuando está vacío (`{}`), igual que `descartes_por_motivo` hoy: un campo que aparece y desaparece obliga a ramificar en cada consumidor del log.

**Por qué f-string y `INFO`**: regresión de producción del 2026-10-27 (commit `4e1f5c8`). Los argumentos diferidos de `logging` quedan prohibidos en esta función; el test de parseo de `duracion_s` como `float` es la red.

### D7 — `docs/filtros.md` sí, knowledge base no

`docs/filtros.md` documenta hoy el umbral como global ("Si una corrida supera **50 descartes**…") y muestra una línea de cierre sin `descartes_por_curso`; ambas cosas quedan falsas con este change, así que se actualiza (umbral por curso, campo nuevo, clave `'?'`).

La KB **no se toca**: `knowledge-base/05_reglas_de_negocio.md` §RN-EXT-02 describe el contrato de negocio (descarte registrado, resumen con motivo y duración, nunca silencioso) y no menciona ni el valor ni el alcance del techo. El techo es una decisión operativa de logging, no una regla de negocio; escribirlo en la KB acoplaría una regla de dominio a un detalle de observabilidad que puede cambiar sin cambiar el negocio.

**Pendiente de verificación en la implementación**: `CHANGES.md` describe el techo como ">50 descartes" dentro de la entrada **archivada** C-11. Esa entrada es historia y no se edita (regla dura 4); lo que sí corresponde es agregar la entrada `C-12` nueva con el alcance corregido.

## Risks / Trade-offs

- **[Volumen de log hasta 3× por corrida]** → acotado por `50 × n_cursos`; el cierre sigue siendo una línea y cada curso queda con su techo. Si en el futuro molesta, se baja el umbral (una constante), no se cambia el diseño.
- **[Un curso con muchísimos descartes sigue siendo parcialmente ciego]** → sí: 130 descartes en `723` muestran 50 líneas y el resto sólo se cuenta. El desglose `descartes_por_curso` hace visible ese excedente (`omitido=15` en el ejemplo), así que la omisión es medible y no silenciosa.
- **[Cambio de formato del cierre puede romper consumidores del log]** → el único consumidor conocido es lectura humana en la pestaña Logs de EasyPanel y asserts de test; los campos previos conservan nombre y posición relativa, y el campo nuevo es aditivo.
- **[Orden lexicográfico de ids de curso confunde]** → documentado en D4 y en `docs/filtros.md`; el contrato es estabilidad, no orden numérico.
- **[Clave `'?'` podría invitar a "arreglarla" inventando un curso]** → el scenario *Descarte sin curso identificable* lo prohíbe explícitamente en el spec.
- **[El detalle ya no se corta a la mitad de la corrida]** → es el objetivo; el riesgo residual es que la línea de `sin_sesion` se cuente dos veces en la percepción del operador (una línea de campus caído + una línea de descarte). Ambas son distintas y ya existen hoy; el desglose por curso las cuenta una sola vez porque sólo `registrar()` incrementa contadores.

## Migration Plan

1. Implementar con TDD sobre la rama de trabajo: tests rojos primero, `PYTHONPATH=src pytest` en verde antes de tocar nada más.
2. Sin migración de datos: `estado.json` no cambia de formato ni de contenido.
3. Deploy: reemplaza el contenedor como cualquier otro cambio de código; no requiere reiniciar Evolution ni re-vincular WhatsApp.
4. Rollback: revertir el commit. El único efecto persistido son líneas de log del formato nuevo durante la ventana entre deploy y rollback.
5. Verificación en vivo: leer la línea de cierre de la próxima corrida real en la pestaña Logs y confirmar que aparecen los tres ids de curso. **No usar `--dry-run` en producción** (`cycle.py:56` marca estado igual que un envío real).

## Open Questions

_(ninguna)_
