# Preguntas Abiertas

## Inconsistencias detectadas

### IN-01 — Nombre de la key de Evolution
**`docs/whatsapp.md` dice**: `EVO_API_KEY`. **`.env.example`/tasks dicen**: `EVO_API_KEY` y `EVO_BASE_URL` (coherentes entre sí). **Impacto**: bajo, pero unificar antes del deploy. **Resolución propuesta**: fijar `EVO_API_KEY` + `EVO_BASE_URL` y corregir donde difiera.

### IN-02 — Etiqueta de vencimiento en plantilla [RESUELTA]
**Resolución**: normalización a `Cierra:` permanente (revisable a futuro). Ver RN-FMT-02.

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|-----------|----------|---------|---------|
| Alta | Completar alias de profesores por comisión (más allá de Yácomo) y revisar exclusion list antes del go-live | 10.3 go-live | Operador |
| Alta | Ejecutar las 6 verificaciones vivas pendientes (2.1, 9.1–9.3, 10.2, 10.3) en el VPS | Cierre del proyecto | Operador |

## Resueltas (registro)

- **Alias `Cierra:` vs `Cierre:`** → se mantiene la normalización a `Cierra:` (RN-FMT-02).
- **Links en mensajes** → no se agregan nunca; mensajes siempre informativos (RN-FMT-03, DD-06).
- **Detección de cambios de fecha** → SÍ entra en alcance: re-aviso en 8:00/20:00 con marca `fecha de entrega modificada` (RN-URG-04, DD-08). Pendiente: change nuevo para specs/design/tasks (el archivado no se toca).
- **Año en fecha** → no se muestra ni se registra; comparación y display solo día/mes/hora (RN-FMT-01, RN-URG-04).
- **Alcance de la 5** → change nuevo `date-change-watch` (specs/design/tasks); el archivado `moodle-extraction` no se toca.
