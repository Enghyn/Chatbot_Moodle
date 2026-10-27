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

Si una corrida supera **50 descartes**, el detalle uno por uno se sustituye por
un resumen agregado con el conteo por motivo (si no, el log se inunda de ruido
conocido).

## Resumen de cierre de corrida

Cada corrida emite **un** resumen, que hace observable el costo (~93 s medidos
en producción para 3 cursos × ~44 secciones):

```
corrida: secciones=44 actividades=57 candidatas=6
         descartes_por_motivo={'sin_fecha': 5, 'sin_id': 1} duracion_s=93.4
```

Por debajo del umbral de descartes es `INFO`; por encima sube a `WARNING` porque
el detalle uno por uno fue omitido.
