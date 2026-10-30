# Design

## Context

Ver `proposal.md` §Why para la causa raíz y la evidencia de producción. Este documento asume ese diagnóstico cerrado.

Estado actual relevante (leído antes de diseñar):

- `state.py:26-33` — `__init__` crea `self._data = {}` y sólo reemplaza por el JSON leído si `path.exists()`; los fallos de decodificación caen en `except (json.JSONDecodeError, OSError): self._data = {}`. No hay log, ni estado observable de por qué arrancó vacío.
- `state.py:42` — `tmp = self.path.with_name(self.path.name + ".tmp")`, nombre fijo.
- `state.py:49-58` — `mark_seen(aid, now, due)` crea la entrada, setea `visto` con `setdefault` y `cierre_base` si falta; cada mutación llama `_save()`.
- `watcher.py:41-58` — `partition_urgent` llama `store.mark_seen(aid, now, due)` **antes** de decidir si la candidata se alerta (`watcher.py:47-48`), y `select_urgent` documenta que el llamador actualiza base y marca urgente tras el envío exitoso.
- `cycle.py:52-72` — el envío ocurre, y `if sent or dry_run:` envuelve el `mark_seen` de **todas** las candidatas, más `mark_notified` y `set_base`.
- `formatting.py:94-97` — `format_digest(candidates, run_date)` formatea **todas** las candidatas de la ventana; no filtra por `is_new` ni consulta el estado. Confirmado por lectura: un digest fallido no "pierde" su contenido por no marcar nada.
- `scrape.py:163-192` — `collect_candidates` cierra con `_resumen_cierre(...)` y una única línea `corrida: secciones=... duracion_s=...` en `INFO`; `scrape.py` no conoce el `StateStore` (lo crea `main.tick`, `main.py:70`, antes de `build_targets`).
- `main.py:57-59` — `state_path()` lee `ESTADO_PATH` con default `estado.json`; `main.py:70` construye el `StateStore` una vez por corrida.
- `tests/test_state_atomic.py:54` — el test de corte usa `self.suffix == ".tmp"` para interceptar el temporal: el nombre único debe **conservar** el sufijo `.tmp`.
- `tests/test_date_change.py:19-35` — la migración sin `cierre_base` exige que la adopción de base sea silenciosa y deje `is_new` en `False`. Cualquier cambio de orden no puede romperlo.

Restricciones: sin cambios de formato ni de texto del mensaje (decisión del usuario), TDD con test rojo primero (regla dura 5), un envío por corrida (regla dura 8), nunca secretos en logs (regla dura 1), archivos archivados intocables (regla dura 4).

## Goals / Non-Goals

**Goals:**
- Que una pérdida del estado persistido se lea en segundos desde el log, sin abrir el contenedor.
- Que un envío fallido no destruya el aviso: la corrida siguiente lo reintenta.
- Que un envío fallido del digest no produzca una ráfaga de 🆕 al día siguiente ni una semana de silencio: la corrida siguiente reintenta el digest completo.
- Que dos escritores concurrentes nunca compartan el archivo temporal.

**Non-Goals:**
- Persistir el estado por sí solo: el volumen en `/data` es acción de infraestructura del operador (ver proposal §Fuera de alcance).
- Cambiar el formato o el texto del mensaje de WhatsApp, o agregar líneas de advertencia dentro del mensaje.
- Cambiar la semántica de `dry_run` (hoy persiste igual que un envío exitoso) ni el margen de 7 días, la ventana de 14 días o los filtros.
- Agregar locking entre procesos: `os.replace` sigue siendo la única primitiva de publicación.
- Migrar `estado.json` ni cambiar las claves de registro existentes: sólo se agrega la clave reservada `__meta__` (D8).

## Decisions

### D1 — La carga del estado se clasifica y se loguea; el envío no cambia

`StateStore.__init__` calcula una clasificación de una sola vez y la expone como atributo de sólo lectura `estado` (valores `ausente` | `vacio` | `corrupto` | `ok`). La clasificación describe **cómo arrancó la corrida**; no se recalcula al guardar.

| Clasificación | Condición | `_data` resultante |
|---|---|---|
| `ausente` | `self.path` no existe | `{}` |
| `vacio` | existe, y está en blanco (0 bytes o sólo espacios) | `{}` |
| `vacio` | existe, decodifica a objeto sin registros (`{}`) | `{}` |
| `corrupto` | existe, y `json.loads` lanza `JSONDecodeError` o `OSError` al leer | `{}` |
| `corrupto` | decodifica pero no es un `dict` (p.ej. `null`, `[]`, `"x"`) | `{}` |
| `ok` | decodifica a un `dict` no vacío | el dict leído |

Formato exacto del warning (una sola línea, nivel `WARNING`, interpolada con f-string, siempre en ese orden de campos):

```
estado=<ausente|vacio|corrupto> ruta=<ruta configurada> motivo=<motivo> accion=arranca_con_estado_vacio_puede_renotificar
```

`motivo` es un token estable y greppable: `archivo_inexistente` (ausente), `sin_contenido` u `objeto_sin_registros` (vacio), `json_invalido`, `tipo_no_objeto` o `error_lectura` (corrupto). Ejemplo real de producción tras un deploy sin volumen:

```
2026-10-28 20:00:03,412 WARNING bot_moodle.state: estado=ausente ruta=/data/estado.json motivo=archivo_inexistente accion=arranca_con_estado_vacio_puede_renotificar
```

**Por qué se envía igual (fail-open)**: lo decidió el usuario y es la política correcta para este dominio — un falso aviso cuesta un mensaje de más y un minuto de vergüenza; un aviso perdido cuesta una entrega. Además el comportamiento de envío **ya es** fail-open hoy (`_data = {}` → todo nuevo → todo se envía): este change no cambia la política, sólo la hace legible. Degradar a "no notificar" ante estado ilegible sería el default de la regla dura 2 aplicado a un dato que **sí** se leyó del campus; no aplica.

**Por qué `{}` cuenta como `vacio` y no como `ok`**: en el código actual no existe un camino que escriba `{}` (todas las mutaciones agregan o modifican una entrada), así que un archivo con `{}` sólo puede venir de una pérdida o de una intervención manual. Tratarlo como `ok` escondería exactamente el caso que hay que diagnosticar; el costo de tratarlo como `vacio` es un warning en una situación que ya se comporta como vacía.

**Por qué no se loguea el contenido**: el archivo contiene ids, títulos y fechas (el mismo dato del mensaje), pero volcarlo agrega volumen y no ayuda al diagnóstico. Ruta + motivo alcanzan para decidir qué hacer.

**Bug extra cubierto (reportado en el proposal)**: `json.loads` puede devolver `None`/`list`/`str`; hoy `_data` quedaría con ese valor y `is_new` (`state.py:47`) reventaría con `TypeError`, matando la corrida con código 1. La validación de tipo de D1 lo clasifica como `corrupto` en vez de reventar.

### D2 — Semántica: avistaje ≠ notificación

| Concepto | Campos | Cuándo se persiste |
|---|---|---|
| **Avistaje** ("ya lo vi") | `visto`, y `cierre_base` en el primer avistaje | **Siempre** que la corrida procese la candidata: al avistarse o al finalizar la corrida, haya enviado o no. Es lo que evita el 🆕 repetido. |
| **Notificación** ("ya te avisé") | `notificado_urgente`, `notificado_digest`, y la **actualización** de `cierre_base` | **Sólo tras `ok=True`** (o `dry_run`, que se mantiene equivalente a un envío exitoso). |

`cierre_base` nace en el avistaje (es una fecha de comparación, no una marca de envío) pero sólo se **actualiza** después de un envío exitoso: por eso un re-aviso fallido sigue siendo detectable en la corrida siguiente (`watcher.is_date_change` compara contra la base vieja).

Consecuencias explícitas:

- **Lo que no se envía se marca visto de inmediato**: en `partition_urgent`, las candidatas fuera del margen de 7 días y las conocidas sin base (migración) se siguen marcando vistas en la misma corrida, como hoy. Si no, al entrar en la ventana de 7 días se notificarían por primera vez y cambiaría el comportamiento actual (`test_integrada_margen_amplio_va_al_digest_y_actualiza_base`, `test_migracion_estado_viejo_adopta_base_sin_alertar`).
- **Lo que se envía se marca visto recién tras `ok=True`**: si el envío falla, la candidata conserva `visto` ausente/previo y la corrida siguiente la vuelve a seleccionar (por `is_new` o por cambio de base) y reproduce el mensaje original, marcas 🆕 incluidas. Es la única forma de reintentar sin agregar un campo persistido nuevo y sin que el reintento salga con las entregas sin marca.

### D3 — `partition_urgent` persiste sólo lo que no va a enviar

```
for cand in candidates:
    due = cand["due"]; si due es None o due < now →  seguir (sin tocar estado)
    if store.is_new(aid):
        if margen <= 7 y not store.was_notified(aid, "urgente"):
            new_urgent.append(cand)        # sin mark_seen: lo persiste el ciclo tras ok=True
        else:
            store.mark_seen(aid, now, due) # fuera de margen: avistaje inmediato (sin cambio)
        continue
    if store.get_base(aid) is None:
        store.mark_seen(aid, now, due)     # migración: adopta base sin alertar (sin cambio)
        continue
    if is_date_change(...) y margen <= 7:
        changed_urgent.append(cand)        # sin tocar base: la actualiza el ciclo tras ok=True
```

`select_urgent` (usado por tests) conserva su firma y su contrato de "el llamador persiste la notificación tras el envío exitoso".

**Alternativa descartada — marca persistida de "envío pendiente"** (p.ej. `envio_fallido: true` para reintentar manteniendo el avistaje siempre). Se descarta porque obliga a un campo nuevo en `estado.json`, a limpiarlo en cada éxito y a decidir con qué marca sale el reintento: al no ser `is_new`, `format_update` lo listaría sin `🆕 NUEVA` bajo un encabezado "0 entrega(s) nueva(s)". D3 consigue el reintento y conserva las marcas sin tocar el formato del estado.

### D4 — Orden de persistencia en `run_cycle`, por rama

**Rama digest (lunes, o reintento pendiente — ver D8)**:

```
if now.weekday() == 0 or store.digest_pendiente:
    text = format_digest(candidates, now)     # mismo texto, sin 🆕
    sent = enviar(...)                        # puede fallar
    for c in candidates: store.mark_seen(...)          # SIEMPRE (avistaje)
    if sent or dry_run:
        store.clear_digest_pendiente()
        for c in candidates:
            store.mark_notified(c["id"], "digest")
            store.set_base(c["id"], c["due"])
    else:
        store.mark_digest_pendiente()          # la corrida siguiente reintenta
```

Un digest fallido deja las candidatas **vistas** (el martes no hay ráfaga de 🆕) sin marcar notificación ni base, y enciende `digest_pendiente`: la corrida siguiente reintenta el digest completo (D8).

**Rama update (martes a domingo)**:

```
new_urgent, changed_urgent = partition_urgent(...)   # ya persistió lo que no se envía
if nothing: return silence
text = format_update(candidates, new_ids, changed_ids)
sent = enviar(...)
if sent or dry_run:
    for c in candidates: store.mark_seen(...)        # avistaje de lo enviado
    for aid in new_ids | changed_ids: store.mark_notified(aid, "urgente")
    for aid in changed_ids: store.set_base(aid, due)
```

Si `sent` es `False` no se persiste nada sobre las candidatas del mensaje: `partition_urgent` ya dejó vistas las que no se alertaban, y las alertadas quedan pendientes para la corrida siguiente.

**Decisión que el usuario debe revisar (P-1)**: la indicación "el avistaje de todas las candidatas se persiste aunque `sent` sea False" se cumple **en la rama digest** y **para las candidatas que no se envían** en la rama update, pero **no** para las candidatas del mensaje urgente que falló, porque marcarlas vistas haría que el reintento de (d) nunca ocurra (quedarían conocidas, con base, sin cambio de fecha) o, si se agregara un campo de pendiente, que el reintento pierda las marcas 🆕. El bug diagnosticado (3) era la ráfaga de 🆕 del **digest** y ese caso queda cubierto sin excepción. No hay otra combinación que satisfaga (d) y (e) a la vez sin cambiar el formato del mensaje. (D8 agrega un flag de pendiente **sólo para el digest**, donde el texto del reintento es el digest completo y por diseño no lleva marcas 🆕; P-1 sigue vigente para la rama update.)

**`dry_run` se mantiene igual que hoy**: se comporta como un envío exitoso para la persistencia (marca visto, notificado y base). Cambiarlo sería una alteración de comportamiento no pedida, y la verificación en vivo de este proyecto ya tiene la regla operativa de no usar `--dry-run` en producción (`docs/filtros.md`, C-11 §D6).

### D5 — Nombre único del temporal

```
tmp = self.path.with_name(f"{self.path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
```

- Conserva el sufijo `.tmp` (lo necesita `tests/test_state_atomic.py`).
- `pid` identifica al proceso y `uuid4().hex` desambigua dos escrituras del mismo proceso.
- Se escribe con `write_text(...)`, se publica con `os.replace(tmp, self.path)` y, si algo falla antes de publicar, el propio temporal se borra (`tmp.unlink(missing_ok=True)` en el camino de error).
- No se hace limpieza global de `*.tmp` al iniciar: borrar temporales ajenos podría matar una escritura viva de otro proceso. Un temporal huérfano de una caída queda en disco, no afecta al archivo real y es visible con `ls /data`.
- Sin locking: dos procesos siguen siendo last-writer-wins sobre el archivo real; lo que se elimina es la corrupción cruzada del temporal.

**Alternativa descartada — `os.open(..., O_CREAT|O_EXCL)` + `flock`**: agrega complejidad de plataforma (Windows/POSIX) para un bot personal single-tenant donde la concurrencia real es "un deploy que se solapa con una corrida". El nombre único ataca el riesgo concreto (pisarse el `.tmp`) sin locking.

### D6 — El campo `estado=` va al final de la línea de cierre existente

La línea que ya emite `scrape._resumen_cierre` queda, tal cual, así:

```
corrida: secciones=91 actividades=163 candidatas=15 descartes_por_motivo={'sin_fecha': 148, 'sin_id': 113} descartes_por_curso={'14': 11, '723': 130, '743': 120} duracion_s=98.6 estado=ok
```

y con truncamiento de detalle:

```
corrida: secciones=91 actividades=163 candidatas=15 descartes_por_motivo={...} descartes_por_curso={...} duracion_s=98.6 descartes_detalle_omitido=15 estado=ausente
```

`estado=` es **siempre el último campo**, para que un parser por regex no dependa de la presencia de `descartes_detalle_omitido`.

Plomería: `collect_candidates` gana el parámetro opcional `estado: str | None = None`; `main.tick` lo alimenta con `store.estado` en el `fetch` (el `StateStore` ya se construye antes, `main.py:70`):

```
fetch=lambda: collect_candidates(sessions, targets, estado=store.estado)
```

Cuando `estado` es `None` (llamadas directas al scrapeo, tests de secciones) el campo se omite: la línea queda exactamente como hoy y ningún test existente cambia. Toda corrida del bot pasa por `main.tick`, así que en producción el campo siempre está.

**Alternativa descartada — una segunda línea de cierre en `run_cycle`**: duplicaría el concepto de "cierre de corrida" y obligaría a leer dos líneas para reconstruir una corrida.

### D7 — Los tests de dos corridas usan el mismo path, no el mismo objeto

Los escenarios de (a), (d) y (e) se escriben con **dos `StateStore` consecutivos sobre el mismo `tmp_path`**, no reutilizando la instancia: así se prueba también la recarga desde disco, que es el punto exacto donde el bug de producción se manifestó (`state.py:29`). Reutilizar la instancia dejaría el bug invisible.

### D8 — Reintento del digest pendiente (`__meta__.digest_pendiente`)

**Problema que cierra**: el avistaje del digest es incondicional (D4), así que si el envío del lunes falla las candidatas quedan vistas y el vigía del martes calla. Sin D8 el contenido sólo reaparecía **el lunes siguiente**: hasta 7 días de silencio para un bot cuyo trabajo es avisar vencimientos. Eso contradice la decisión explícita del usuario para el caso análogo (estado perdido: aviso > silencio) y empeora el defecto 3 del proposal: se cambiaba una ráfaga de 🆕 por una semana muda.

**Decisión del usuario (vinculante)**: si el envío del digest falla, la corrida siguiente reintenta el **digest completo**, una sola vez por corrida programada (regla dura 3: sin bucles activos).

**Representación**: una clave reservada de metadatos en el mismo `estado.json`, sin tocar el mapa plano de registros:

```json
{
  "__meta__": {"digest_pendiente": true},
  "56812": {"visto": "2026-10-05T08:00:00", "notificado_digest": true}
}
```

- El nombre no puede colisionar con un registro: los `assign id` de Moodle son numéricos.
- `StateStore.digest_pendiente` (bool, default `False`) tolera archivos viejos sin `__meta__` y un `__meta__` que no sea objeto (`"x"`, `null`, `[]`, `5`).
- `mark_digest_pendiente()` / `clear_digest_pendiente()` mutan a través de `_save()` (temporal único + `os.replace`, D5). Sin cambio observable no se reescribe: un digest exitoso no crea `__meta__` y, al apagarse el flag, la clave se borra, así que el archivo vuelve a su forma previa.
- `is_new`, `get_base` y `was_notified` no consultan `__meta__`: el flag no puede convertir una entrega en "vista" ni en "notificada".

**Efecto en `run_cycle`**: la rama digest se elige con `now.weekday() == 0 or store.digest_pendiente`; tras el envío, `sent or dry_run` limpia el flag y, en caso contrario, lo enciende. El texto es el de `format_digest` tal cual (encabezado `*Comisión 4 - Vencimientos (<día>)*`, sin `🆕`): el reintento **no** es un update, así que no hay ráfaga de 🆕 y una entrega que apareció entre el fallo y el reintento entra en la misma lista, una sola vez. El avistaje sigue siendo incondicional y `notificado_digest`/`set_base` siguen condicionados a `sent or dry_run` (D4 intacto). `dry_run` no enciende el flag, coherente con el resto del change (equivale a un envío exitoso).

**Alternativa descartada — no persistir el avistaje del digest fallido** (dejar todo `is_new` para que el martes lo levante el vigía). Reintenta, sí, pero como **update**: `format_update` marcaría cada candidata con `🆕 NUEVA` y el encabezado diría "N entrega(s) nueva(s)" para entregas que no son nuevas (algunas con 13 días de margen, fuera del umbral urgente). Es exactamente la ráfaga de 🆕 que el change dice arreglar, además de romper la tarea 4.7 (`get_base` no podría quedar en `None` si el avistaje se pierde) y de cambiar el ritmo 8:00/20:00.

**Alternativa descartada — reintentar dentro de la misma corrida** (loop hasta `ok=True`): viola la regla dura 3 (nada de reintentos en bucle ante fallos de envío) y multiplicaría los POST a Evolution con la sesión caída. El reintento es una decisión por corrida, no un bucle.

## Risks / Trade-offs

- **[El warning de estado aparece en cada deploy mientras no haya volumen]** → Es el objetivo. Falso positivo aceptado: `accion=arranca_con_estado_vacio_puede_renotificar` dice exactamente qué va a pasar.
- **[Una renotificación sigue siendo posible tras un deploy sin volumen]** → Riesgo aceptado por decisión del usuario; la mitigación real (volumen en `/data`) es del operador. Este change sólo garantiza que el log lo explique.
- **[La rama update no marca visto lo que falló]** → Si el envío falla muchas corridas seguidas, cada corrida reintenta el mismo mensaje. Es el comportamiento buscado (reintento por corrida, no bucle dentro de una corrida: regla dura 3 se respeta, un POST por corrida) y el mensaje es idéntico al original.
- **[Un digest pendiente altera el ritmo del día siguiente]** → La corrida que reintenta manda un digest fuera del lunes, y ese día no manda update aunque haya una urgente nueva: un solo `send_text` por corrida (regla dura 8). Se acepta: la urgente entra en el digest reintentado (sin `🆕`, porque el digest no lleva marcas) y el vigía del 20:00 vuelve al ritmo normal.
- **[El flag vive en el mismo archivo que el resto del estado]** → Si el estado se pierde (deploy sin volumen), se pierde también el flag y el reintento; esa corrida arranca con todo nuevo y avisa igual (fail-open), que es el riesgo ya aceptado sin volumen.
- **[`estado=vacio` con `{}` puede ser una intervención manual legítima]** → Un warning en ese caso es barato y documentable; el silencio es lo caro.
- **[Temporales huérfanos en `/data`]** → No afectan la lectura (el nombre real es `estado.json`) y son visibles; limpiarlos automáticamente es más riesgoso que dejarlos.
- **[Los tests de concurrencia no prueban interleaving real de dos procesos]** → Se prueban las dos propiedades deterministas que eliminan el bug: nombre único por escritura y no pisar un temporal ajeno. Un test de carrera real sería no determinista y con `pytest` en Windows daría flakiness.

## Migration Plan

1. Implementar en el orden de `tasks.md` (test rojo primero por cada punto), con la suite completa en verde antes de cualquier deploy.
2. Sin migración de datos: el formato de los registros por `assign id` no cambia y las entradas viejas sin `cierre_base` siguen adoptando la base sin alertar. La clave reservada `__meta__` sólo aparece mientras hay un digest pendiente (D8).
3. Deploy: reemplaza la imagen. La primera corrida posterior a un deploy sin volumen emitirá `estado=ausente` + warning; si el operador ya montó el volumen, emitirá `estado=ok`.
4. Rollback: revertir el commit. Los efectos persistidos nuevos son el avistaje de las candidatas de un digest fallido (en el peor caso evita un 🆕 de más, no pierde avisos) y la clave `__meta__`, que el código anterior ignora por completo (ningún `assign id` es `__meta__`).

## Open Questions

- _(ninguna)_ — La decisión pendiente de revisión es P-1 (ver D4): el alcance exacto de "avistaje siempre" en la rama update fallida. Está resuelta en el diseño a favor de que (d) funcione, y se deja señalada para el usuario.
