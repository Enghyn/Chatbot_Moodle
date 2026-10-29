# Regla temporal del bot

Solo se notifican vencimientos **no vencidos dentro de 14 días** desde el día
de ejecución, ordenados de más urgente a menos urgente (fecha fin ascendente).

## Casos verificados (reloj fijo: 29 sept 2026, 8:00)

1. **Incluye 3 días**: vence el 2 oct 2026 → candidata (entra en ventana).
2. **Excluye 20 días**: vence el 19 oct 2026 → se guarda sin notificar.
3. **Excluye vencida**: UML (Cierre 25 de agosto de 2026) evaluado el 29 sept →
   no aparece en el mensaje de esa semana.

## Borde

- Vence exactamente a los 14 días → entra.
- Vence a los 14 días + 1 segundo → espera.

Ver `tests/test_temporal.py` y `tests/test_docs_filtros.py`: los ejemplos de
este doc coinciden con los tests.

## Qué pasa con lo que se descarta antes de la ventana

El descarte por falta de fecha de cierre **deja `warning` en el log** (ya no es
silencioso). Cada línea trae el motivo, el id, el título, el tipo de módulo, el
curso y la sección:

```
descarte motivo=sin_fecha id=56812 titulo='Trabajo Práctico Unidad 4 (Semana 8) Tarea'
        modtype=assign curso=723 seccion=40 (Práctica 💻)
```

Motivos: `sin_fecha` (sin cierre parseable), `sin_id` (sin identidad determinable
— nunca se usa el id del curso), `detalle_fallo`, `seccion_fallo`, `sin_sesion`.

Nunca se loguean cookies, `MoodleSession`, `logintoken`, `sesskey`, usuario ni
password: solo el mismo conjunto de datos que ya viaja en el mensaje.

Si un **curso** supera **50 descartes**, el detalle uno por uno de ese curso se
corta ahí: sus descartes restantes sólo se cuentan (si no, el log se inunda de
ruido conocido). El techo es **por curso y no por corrida**: así el ruido de un
curso no deja ciego al siguiente, sin importar el orden en que se recorren los
targets. Una corrida con 3 cursos puede emitir hasta ~150 líneas de detalle.

Nunca se omitió nada en silencio: lo que no salió como línea de detalle aparece
en el desglose del cierre.

## Resumen de cierre de corrida

Cada corrida emite **un** resumen, que hace observable el costo (~93 s medidos
en producción para 3 cursos × ~44 secciones):

```
corrida: secciones=44 actividades=57 candidatas=6
         descartes_por_motivo={'sin_fecha': 5, 'sin_id': 1}
         descartes_por_curso={'14': 3, '723': 2, '743': 1} duracion_s=93.4 estado=ok
```

(En el log es una sola línea; acá se muestra partida por ancho.)

- `descartes_por_motivo` — cuántos descartes hubo de cada motivo en la corrida.
- `descartes_por_curso` — cuántos descartes hubo en cada curso. Es el campo que
  muestra el desbalance de un vistazo: un curso entero sin sesión, o con mucho
  ruido, se ve acá aunque su detalle se haya cortado.
  - Las claves salen **ordenadas** de forma determinista (orden lexicográfico de
    los ids como texto: `'14'`, `'723'`, `'743'`). Mismo conjunto de descartes ⇒
    misma línea, byte a byte, sin importar el orden de recorrido.
  - La clave `'?'` significa **curso desconocido**: el descarte llegó sin
    `course_id` (ausente o vacío). Nunca se inventa un id de curso para tapar el
    hueco.
  - El campo se emite siempre, también vacío (`{}`).
- `duracion_s` — duración real de la corrida, parseable como número.
- `descartes_detalle_omitido=N` — sólo aparece si hubo truncamiento, y es la
  **suma de los excedentes por curso**, no el total menos el umbral. Con 60
  descartes en `723`, 55 en `743` y 11 en `14`: `(60−50) + (55−50) + 0 = 15`.
- `estado=` — **siempre el último campo de la línea**, para que un parser por
  regex no dependa de la presencia de `descartes_detalle_omitido`. Es la
  clasificación con la que se cargó `estado.json` en esa corrida:
  `ausente` (el archivo no existe), `vacio` (existe pero está en blanco o sin
  registros), `corrupto` (no decodifica o no es un objeto) u `ok` (se leyó
  bien). Ver `docs/estado.md` §Carga y diagnóstico.

  Cómo leerlo en EasyPanel: abrir la pestaña **Logs** del servicio y buscar
  `corrida:`; el último token de la línea dice si la corrida arrancó con estado
  sano. `estado=ausente`, `estado=vacio` o `estado=corrupto` significa que esa
  corrida **puede renotificar** entregas ya avisadas (el bot envía igual:
  fail-open), y que falta montar el volumen persistente en `/data` (acción del
  operador, fuera del código). Si el parámetro no se pasa (llamadas directas al
  scrapeo), el campo se omite y la línea queda como antes.

El resumen es siempre `INFO`: es información operativa, no una anomalía. El
`WARNING` queda reservado a los descartes individuales, y no hay un warning
aparte "por resumen agregado" (esa duplicación se retiró).
