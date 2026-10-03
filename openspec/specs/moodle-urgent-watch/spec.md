# Moodle Urgent Watch Specification

## Purpose

Detectar entre digest semanales las entregas nuevas que vencerían antes de ser notificadas, y alertarlas de inmediato sin spamear.

## Requirements

### Requirement: Detección de entregas nuevas
El sistema SHALL registrar cada `assign id` visto con fecha de primer avistaje y fecha base de cierre (día/mes/hora) para distinguir nuevas de ya conocidas y detectar cambios.

#### Scenario: Primer avistaje
- **WHEN** una corrida encuentra un id nunca visto con fecha de cierre parseable
- **THEN** lo marca como nuevo con timestamp de descubrimiento y guarda su cierre como base de comparación

#### Scenario: Ya conocida
- **WHEN** una corrida encuentra un id ya registrado con igual día/mes/hora de cierre que la base
- **THEN** no lo trata como nuevo aunque siga en ventana (lo cubre el digest)

### Requirement: Re-aviso por cambio de fecha
El sistema SHALL re-notificar en la corrida 8:00/20:00 que detecte el cambio toda entrega conocida cuyo día/mes/hora de cierre difiera de la base, con la marca `fecha de entrega modificada`, y actualizar la base.

#### Scenario: Cambio de día con margen urgente
- **WHEN** una entrega conocida pasa de vencer en 10 días a vencer en 3 días
- **THEN** se re-avisa en esa corrida con la marca y la base pasa al nuevo cierre

#### Scenario: Cambio con margen amplio
- **WHEN** una entrega conocida cambia su cierre pero el nuevo margen supera 7 días
- **THEN** no se alerta; la fecha actualizada aparece en el próximo digest y la base se actualiza igual

#### Scenario: Cambio solo de año
- **WHEN** solo cambia el año del cierre (igual día/mes/hora)
- **THEN** no se re-avisa (el año se ignora en la comparación)

#### Scenario: Segundo cambio distinto
- **WHEN** una entrega ya re-avisada vuelve a cambiar su cierre a otro valor
- **THEN** se re-avisa de nuevo (cada cambio distinto avisa una vez)

### Requirement: Umbral urgente de 7 días
El sistema SHALL alertar de inmediato solo las nuevas cuyo margen `vencimiento - hoy <= 7 días`; las de mayor margen SHALL esperar al próximo digest.

#### Scenario: Nueva urgente (margen corto)
- **WHEN** se descubre un martes una entrega que vence al día siguiente (margen 1)
- **THEN** se alerta en esa misma corrida

#### Scenario: Nueva al límite
- **WHEN** se descubre un martes una entrega que vence en 7 días
- **THEN** se alerta en esa misma corrida (llegaría al lunes con 1 día, insuficiente)

#### Scenario: Nueva con tiempo
- **WHEN** se descubre un martes una entrega que vence en 10 días
- **THEN** no se alerta; aparece en el digest del lunes con 4 días de margen

### Requirement: Alerta en la misma lista con resaltado
El sistema SHALL enviar la alerta urgente al mismo destino con la misma lista ordenada por fecha, encabezado `Actualización - N nueva(s)` y marca 🆕 solo en las nuevas.

#### Scenario: Una nueva
- **WHEN** hay 1 entrega nueva urgente entre 5 candidatas
- **THEN** el mensaje lleva encabezado de actualización con contador 1 y una sola marca 🆕

#### Scenario: Sin novedades
- **WHEN** una corrida del vigía no encuentra nuevas urgentes
- **THEN** no envía ningún mensaje (silencio total)

### Requirement: Ritmo 8:00 y 20:00 con digest integrado
El sistema SHALL correr el vigía a las 8:00 y 20:00 todos los días; la corrida del lunes 8:00 SHALL incluir además el digest semanal de 14 días.

#### Scenario: Corrida nocturna con hallazgo
- **WHEN** la corrida de las 20:00 descubre una urgente subida al mediodía
- **THEN** la alerta sale esa noche (punto ciego máximo ~12h)

#### Scenario: Alerta única
- **WHEN** una urgente ya fue alertada en una corrida previa
- **THEN** las corridas siguientes no la re-alertan (el digest la sigue listando sin marca)
