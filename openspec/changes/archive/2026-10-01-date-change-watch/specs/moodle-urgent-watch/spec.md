# Spec Delta

## MODIFIED Requirements

### Requirement: Detección de entregas nuevas
El sistema SHALL registrar cada `assign id` visto con fecha de primer avistaje y fecha base de cierre (día/mes/hora) para distinguir nuevas de ya conocidas y detectar cambios.

#### Scenario: Primer avistaje
- **WHEN** una corrida encuentra un id nunca visto con fecha de cierre parseable
- **THEN** lo marca como nuevo con timestamp de descubrimiento y guarda su cierre como base de comparación

#### Scenario: Ya conocida
- **WHEN** una corrida encuentra un id ya registrado con igual día/mes/hora de cierre que la base
- **THEN** no lo trata como nuevo aunque siga en ventana (lo cubre el digest)

## ADDED Requirements

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
