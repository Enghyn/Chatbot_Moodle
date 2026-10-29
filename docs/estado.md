# Estado persistente (`estado.json`)

Registro por `assign id`: `{visto, notificado_urgente, notificado_digest, cierre_base}`,
más una clave reservada `__meta__` para flags de la corrida (ver
[`__meta__`](#__meta__-clave-reservada)).

## `cierre_base`

Fecha base de comparación para detectar cambios de fecha. Formato (año
ignorado en la comparación):

```json
"cierre_base": {"d": 9, "m": 10, "h": 23, "mi": 59}
```

- `d`: día del mes, `m`: mes, `h`: hora, `mi`: minuto.
- Se guarda en el primer avistaje (`mark_seen` con `due`) y se actualiza
  con `set_base` tras cada re-aviso enviado (o tras el digest que incluya
  la fecha nueva).
- La comparación ignora el año: solo día/mes/hora/minuto.

## `__meta__` (clave reservada)

Además de los registros por `assign id`, el archivo guarda una clave reservada
para los flags de la corrida. No puede colisionar con una entrega: los
`assign id` de Moodle son numéricos y `__meta__` no lo es.

```json
"__meta__": {"digest_pendiente": true}
```

- `digest_pendiente`: `true` cuando el último digest (el del lunes, o su
  reintento) **no** se pudo enviar. La corrida siguiente lo reintenta completo y,
  cuando sale, el flag se apaga.
- Sólo aparece cuando hay algo pendiente: un digest exitoso no escribe
  `__meta__`, y al apagarse el flag la clave se borra (el archivo vuelve a su
  forma anterior).
- `is_new`, `get_base` y `was_notified` **nunca** consultan `__meta__`: no es
  una entrega vista, no tiene `cierre_base` y no se marca como notificada.
- Un archivo viejo sin `__meta__`, o con un `__meta__` que no sea un objeto
  (`"x"`, `null`, `[]`, `5`), vale `digest_pendiente == False`: no enciende el
  reintento y no revienta la corrida.

## Carga y diagnóstico

Al arrancar, `StateStore` clasifica **cómo leyó** el archivo y lo expone en
`store.estado`, un atributo de sólo lectura que se calcula una sola vez por
corrida (no se recalcula al guardar).

| `estado` | Cuándo | Qué hace el bot |
|---|---|---|
| `ausente` | el archivo no existe (`motivo=archivo_inexistente`) | arranca vacío: todo se considera nuevo |
| `vacio` | existe pero está en blanco, 0 bytes o sólo espacios (`motivo=sin_contenido`) o decodifica a `{}` (`motivo=objeto_sin_registros`) | arranca vacío: todo se considera nuevo |
| `corrupto` | no decodifica (`motivo=json_invalido`), falla la lectura (`motivo=error_lectura`) o decodifica a algo que no es un objeto, p.ej. `null`, `[]`, `"texto"` (`motivo=tipo_no_objeto`) | arranca vacío: todo se considera nuevo, sin reventar |
| `ok` | decodifica a un objeto (con registros, o sólo con `__meta__`) | respeta lo leído |

Cualquier clasificación distinta de `ok` emite **un único** `WARNING` de una
línea, siempre con el mismo orden de campos:

```
estado=<ausente|vacio|corrupto> ruta=<ruta configurada> motivo=<motivo> accion=arranca_con_estado_vacio_puede_renotificar
```

Ejemplo real de producción, primera corrida después de un deploy sin volumen:

```
2026-10-28 20:00:03,412 WARNING bot_moodle.state: estado=ausente ruta=/data/estado.json motivo=archivo_inexistente accion=arranca_con_estado_vacio_puede_renotificar
```

La línea lleva **sólo** ruta y motivo: nunca el contenido del archivo, ni
cookies, tokens, usuario o contraseña (regla dura 1).

Con estado no sano la corrida **envía igual** (fail-open): la pérdida de
estado nunca silencia un aviso. Lo único que cambia es que ahora se ve en el
log y no hay que abrir el contenedor para descubrirlo. El mismo valor viaja en
el campo `estado=` de la línea de cierre de corrida (ver `docs/filtros.md`).

**Acción del operador (fuera de este código)**: montar un volumen persistente
en `/data` en EasyPanel. El bot no puede persistir el estado por sí solo: la
imagen define `ESTADO_PATH=/data/estado.json`, y sin el mount ese directorio
vive en el _writable layer_ del contenedor y se pierde en cada deploy. Mientras
falte el volumen cada deploy producirá un `estado=ausente` y un 🆕 que es
legítimo desde el punto de vista del bot.

## Migración de estados viejos

Los registros creados antes de este campo no tienen `cierre_base`. En el
próximo avistaje posterior la adoptan silenciosamente del `due` observado,
sin disparar ningún aviso (ver `tests/test_date_change.py`).

## Avistaje vs notificación

Dos conceptos distintos, con dos momentos de persistencia distintos:

| Concepto | Campos | Cuándo se persiste |
|---|---|---|
| **Avistaje** ("ya lo vi") | `visto`, y `cierre_base` en el primer avistaje | **Siempre** que la corrida procese la candidata: haya enviado o no. Es lo que evita el `🆕 NUEVA` repetido. |
| **Notificación** ("ya te avisé") | `notificado_urgente`, `notificado_digest` y la **actualización** de `cierre_base` | **Sólo tras `ok=True`** (o en `--dry-run`, que se mantiene equivalente a un envío exitoso). |

- `visto`: timestamp ISO del primer avistaje (`mark_seen`); nunca se
  sobrescribe.
- `notificado_urgente`: `True` después de enviar el aviso urgente de esa
  entrega.
- `notificado_digest`: `True` después de enviar un digest que la incluía.
- `cierre_base`: nace en el avistaje (es una fecha de comparación, no una
  marca de envío) pero sólo se **actualiza** después de un envío exitoso. Por
  eso un re-aviso fallido sigue siendo detectable en la corrida siguiente:
  `watcher.is_date_change` compara contra la base vieja.

Lo que la corrida **no** envía se marca visto de inmediato en
`partition_urgent`: las nuevas fuera del margen de 7 días y las conocidas sin
base (migración). Si no, al entrar en la ventana de 7 días se notificarían por
primera vez. Lo que **sí** se envía se marca visto recién después de `ok=True`
(ver la sección siguiente).

## Orden de persistencia por corrida

`run_cycle` persiste según la rama, y la diferencia importa cuando el envío
falla (`ok=False`).

### Rama digest (lunes, o reintento pendiente)

1. Envía el digest (todas las candidatas de la ventana de 14 días).
2. **Siempre** persiste el avistaje (`visto`) de todas las candidatas, falle o
   no el envío.
3. Sólo con `ok=True` (o `--dry-run`): `notificado_digest`, `cierre_base` y se
   apaga `digest_pendiente`.
4. Si el envío falla: se enciende `__meta__.digest_pendiente`.

Un digest fallido deja las candidatas vistas, así que **no** hay ráfaga de
`🆕`, y la corrida siguiente (8:00 o 20:00, del día que sea) **reintenta el
digest completo**, no un update: la rama se elige por
`now.weekday() == 0 or store.digest_pendiente`. El texto es el que manda
`format_digest` tal cual (encabezado `*Comisión 4 - Vencimientos (<día>)*`, sin
`🆕`), así que una entrega que apareció entre el fallo y el reintento entra en
la misma lista, una sola vez. Si el reintento también falla, el flag sigue
encendido y se vuelve a probar en la corrida siguiente; nunca hay más de un
`send_text` por corrida. La base del digest se sincroniza recién con el envío
exitoso (por eso, tras un fallo, `get_base` sigue vacío).

### Rama update (cualquier corrida sin digest pendiente, típicamente martes a domingo)

1. `partition_urgent` ya persistió el avistaje de lo que **no** se va a enviar
   (fuera del margen de 7 días, o migración sin base).
2. Si no hay nada que avisar: `{"sent": False, "kind": "silence", "text": ""}`.
3. Envía el update.
4. Sólo con `ok=True` (o `--dry-run`): avistaje de las candidatas del mensaje,
   `notificado_urgente` de las nuevas y las modificadas, y `cierre_base` de las
   modificadas.

Si el envío falla, las candidatas del mensaje **no** se persisten: la corrida
siguiente las vuelve a seleccionar y reintenta el mismo aviso, con su marca
`🆕 NUEVA` o `🔄 fecha de entrega modificada` intacta (un POST por corrida, sin
bucle de reintentos dentro de la corrida).

> ℹ️ **Límite conocido (P-1)**: el "avistaje siempre" se cumple en la rama
> digest y para todo lo que no se envía en la rama update. Para las candidatas
> del mensaje urgente que falló se elige el reintento en vez del avistaje: si
> se marcaran vistas, nunca se reintentarían o el reintento perdería la marca
> `🆕`. No hay combinación que cumpla ambas cosas sin cambiar el formato del
> mensaje.

Ver `src/bot_moodle/cycle.py` (`run_cycle`) y `src/bot_moodle/watcher.py`
(`partition_urgent`).

Ver también `src/bot_moodle/state.py`: `base_of`, `base_matches`,
`StateStore.get_base`, `StateStore.set_base`.

