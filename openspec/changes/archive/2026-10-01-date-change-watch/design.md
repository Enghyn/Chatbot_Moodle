# Design

## Context

Ver proposal.md. El `moodle-urgent-watch` vigente (main spec) solo alerta ids nunca vistos con margen ≤ 7 días; el estado guarda `{visto, notificado_urgente, notificado_digest}` sin fecha base. Este change agrega la rama de cambio de fecha decidida en KB (RN-URG-04, DD-08).

## Goals / Non-Goals

**Goals:**
- Guardar `cierre_base` (día/mes/hora) por id y migrar estados viejos sin el campo.
- Comparar cada corrida contra la base ignorando el año; re-avisos con marca en 8:00/20:00.
- Re-aviso inmediato solo con margen ≤ 7 días; si no, la fecha actualizada sale en el digest.

**Non-Goals:**
- Cambiar extracción, comisiones, envío, scheduling o formato (salvo la marca nueva).
- Historial de cambios (solo vive la base actual; sin log de movimientos).

## Decisions

### 1. Comparación por (día, mes, hora), año ignorado
Por qué: decisión del operador (fecha corta sin año; el año no se registra). Un cambio 2026→2027 mismo día/mes/hora no re-avisa. Alternativa (comparar datetime completo): descartada por decisión explícita.

### 2. Re-aviso con la misma urgencia que un id nuevo
Por qué: un cambio que deja margen ≤ 7 días tiene el mismo riesgo de pasar por alto que una entrega nueva; si el margen es mayor, el digest del lunes lo muestra actualizado. Consistencia con RN-URG-02 en vez de una regla paralela.

### 3. Base actualizada en cada re-aviso (single-shot por cambio)
Por qué: evita re-alertar lo mismo en la corrida siguiente; un segundo cambio distinto vuelve a avisar. Migración: estados sin `cierre_base` la adoptan del primer avistaje posterior sin alertar.

## Risks / Trade-offs

- [Profesor que corrige la fecha varias veces en un día] → Mitigación: cada valor distinto avisa una vez; ruido acotado a cambios reales.
- [Cambio detectado pero corrida sin envío por sesión caída] → Mitigación: la base solo se actualiza tras envío exitoso o digest que la incluya; si el envío falla, la próxima corrida lo reintenta.
