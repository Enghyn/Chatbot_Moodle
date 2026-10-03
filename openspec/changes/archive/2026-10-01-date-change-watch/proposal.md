# Proposal

## Why

Si un profesor mueve la fecha de una entrega ya notificada, el vigía actual la ignora (solo alerta ids nunca vistos) y los estudiantes quedan con información vieja. Al cerrar las preguntas abiertas de la KB se decidió que esto entra en alcance con re-aviso marcado.

## What Changes

- El `estado.json` guarda además la fecha base de comparación (`cierre_base`: día/mes/hora) por `assign id`.
- En cada corrida 8:00/20:00, si una entrega conocida cambió su día/mes/hora de cierre vs la base (año ignorado), se re-notifica en esa corrida con la marca `fecha de entrega modificada` y se actualiza la base.
- Re-aviso inmediato solo si el nuevo vencimiento tiene margen ≤ 7 días; si es mayor, la fecha actualizada aparece en el próximo digest sin alerta.
- Cada cambio distinto re-avisa una vez (nueva base tras cada re-aviso).
- Cambios solo de año no re-notifican. Fecha corta sigue sin año.

## Capabilities

### New Capabilities
- (ninguna)

### Modified Capabilities
- `moodle-urgent-watch`: el estado pasa de vistos/notificados a incluir fecha base; el vigía suma re-aviso por cambio de fecha con marca.

## Impact

- Código: `state.py` (campo `cierre_base` + migración de estados viejos), `watcher.py` (rama de cambio), `formatting.py` (marca `fecha de entrega modificada`), tests nuevos con reloj fijo.
- Sin cambios en extracción, filtros de comisión, envío ni scheduling.
- El change archivado `moodle-extraction` no se toca; este change lo extiende.
