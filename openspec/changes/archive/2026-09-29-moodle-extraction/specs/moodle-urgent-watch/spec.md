# Spec Delta

## Purpose

Detectar entre digest semanales las entregas nuevas que vencerían antes de ser notificadas, y alertarlas de inmediato sin spamear.

## ADDED Requirements

### Requirement: Detección de entregas nuevas
El sistema SHALL registrar cada `assign id` visto con fecha de primer avistaje para distinguir nuevas de ya conocidas.

#### Scenario: Primer avistaje
- **WHEN** una corrida encuentra un id nunca visto con fecha de cierre parseable
- **THEN** lo marca como nuevo con timestamp de descubrimiento

#### Scenario: Ya conocida
- **WHEN** una corrida encuentra un id ya registrado
- **THEN** no lo trata como nuevo aunque siga en ventana (lo cubre el digest)

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
