# Funcionalidades

## Épica 1: Extracción Moodle

### US-001 — Login en ambos campus
**Como** operador **Quiero** sesionar en Campus 1 y 2 con mi cuenta estudiante **Para** leer exactamente lo visible para comisión 4.
**Criterios de aceptación:**
- [ ] CA-1: ambas sesiones válidas con user+pass distintos y misma clave.
- [ ] CA-2: campus fallido se reporta y no bloquea al otro.
**Reglas relacionadas**: RN-EXT-01, RN-TMP-03, RN-GLB-02.

### US-002 — Recorrido y parseo de entregas
**Como** operador **Quiero** extraer todas las actividades con fecha de todas las secciones **Para** no perder entregas fuera de la vista actual.
**Criterios de aceptación:**
- [ ] CA-1: recorre índice completo, no solo `Tema_&section=`.
- [ ] CA-2: parsea alias Apertura/Cierre de ambos campus; sin fecha se descarta.
**Reglas relacionadas**: RN-EXT-02, RN-EXT-03, RN-EXT-04, RN-EXT-05.

### US-003 — Filtros temporal y de comisión
**Como** compañero **Quiero** ver solo lo que me toca y vence pronto **Para** no leer ruido de otras comisiones ni fechas lejanas.
**Criterios de aceptación:**
- [ ] CA-1: ventana 14 días + vencidas fuera (casos de `docs/filtros.md`).
- [ ] CA-2: compartidas con la 4 entran, solo-otras salen, UML-1457 excluido.
**Reglas relacionadas**: RN-TMP-01, RN-TMP-02, RN-COM-01 a RN-COM-04.

## Épica 2: Vigía urgente

### US-004 — Alerta de nuevas urgentes
**Como** compañero **Quiero** que lo subido entre lunes con vencimiento cercano me llegue igual **Para** no enterarme tarde.
**Criterios de aceptación:**
- [ ] CA-1: nueva con margen ≤ 7 días alerta en la corrida que la descubre.
- [ ] CA-2: nueva con margen mayor espera al lunes; sin novedades hay silencio.
- [ ] CA-3: nunca se re-alerta lo ya alertado.
- [ ] CA-4: si una entrega conocida cambia su día/mes/hora de cierre, se re-notifica en la próxima corrida 8:00/20:00 con marca `fecha de entrega modificada`.
**Reglas relacionadas**: RN-URG-01, RN-URG-02, RN-URG-03, RN-URG-04.

## Épica 3: Envío WhatsApp

### US-005 — Digest y alertas al grupo
**Como** operador **Quiero** que el texto llegue al grupo general desde mi número **Para** avisar sin trabajo manual.
**Criterios de aceptación:**
- [ ] CA-1: un envío por mensaje vía Evolution; sesión caída se reporta sin reintentos.
- [ ] CA-2: grupo de prueba primero; general solo con JID final.
**Reglas relacionadas**: RN-ENV-01, RN-ENV-02, RN-ENV-03.

### US-006 — Formato legible y distinguible
**Como** compañero **Quiero** orden fijo por materia y marcas de novedad **Para** encontrar mi materia y notar lo nuevo.
**Criterios de aceptación:**
- [ ] CA-1: orden Prog→BD2→Inglés, fecha corta ES, verbatim con emojis, sin links.
- [ ] CA-2: encabezados digest/actualización/vacío según plantilla.
**Reglas relacionadas**: RN-FMT-01, RN-FMT-02, RN-FMT-03.
