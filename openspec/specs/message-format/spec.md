# Message Format Specification

## Purpose

Definir la plantilla exacta de los mensajes de WhatsApp para que el digest, la alerta urgente y la semana vacía sean predecibles y distinguibles.

## Requirements

### Requirement: Orden fijo de materias con fecha ascendente interna
El sistema SHALL ordenar el mensaje por materias en orden fijo (Programación, BD2, Inglés); dentro de cada materia SHALL ordenar grupos `Unidad - Apartado` y entregas por fecha fin ascendente. Cada grupo SHALL encabezarse en una sola línea `{Unidad} - {Apartado}` (ej. `CSS - Práctica`, `Unidad 4 - Práctica`).

#### Scenario: Tres materias con candidatas
- **WHEN** las tres materias tienen vencimientos en ventana
- **THEN** el mensaje muestra primero Programación, luego BD2, luego Inglés, con cada bloque internamente ascendente por fecha

#### Scenario: Materia sin candidatas
- **WHEN** una materia no tiene entregas en ventana
- **THEN** su bloque no aparece (sin dejar hueco ni encabezado vacío)

#### Scenario: Encabezado unidad-apartado
- **WHEN** una entrega de Programación vive en el apartado `Práctica` bajo la unidad de tab `CSS`
- **THEN** su grupo se encabeza `CSS - Práctica` en una sola línea

#### Scenario: Apartado sin unidad padre
- **WHEN** una actividad no tiene tab de unidad precedente (huérfana o primera tab)
- **THEN** su grupo se encabeza solo con el apartado, como antes del cambio

### Requirement: Fecha corta en español sin links
El sistema SHALL mostrar cada entrega en una línea con título verbatim y fecha corta `sem día mes, hora`; no SHALL incluir links en V1.

#### Scenario: Línea de entrega
- **WHEN** una entrega vence el viernes 10 de octubre a las 23:59
- **THEN** la línea es `- <título> (Cierra: vie 10 oct, 23:59)` (o `Cierre:` según alias de origen, normalizado a formato corto)

#### Scenario: Sin links
- **WHEN** se formatea cualquier entrega en V1
- **THEN** no se incluye URL de Moodle; el mensaje es solo informativo

### Requirement: Encabezados distinguibles por tipo de mensaje
El sistema SHALL encabezar el digest con `*Comisión 4 - Vencimientos (<fecha corrida>)*` y la alerta urgente con `*Comisión 4 - Actualización: N entrega(s) nueva(s)*` más marca 🆕 solo en las nuevas.

#### Scenario: Digest
- **WHEN** es la corrida del lunes 8:00
- **THEN** el encabezado es el de vencimientos con la fecha de la corrida

#### Scenario: Urgente con una nueva
- **WHEN** hay 1 entrega nueva urgente entre candidatas conocidas
- **THEN** el encabezado lleva contador 1 y solo la nueva lleva `🆕 NUEVA`

### Requirement: Semana vacía con aviso corto
El sistema SHALL enviar en el digest del lunes sin candidatas el aviso `Sin entregas con vencimiento hasta la semana que viene, atento a cambios` con el encabezado de vencimientos; el vigía SHALL permanecer en silencio cuando no hay novedades.

#### Scenario: Lunes vacío
- **WHEN** ninguna materia tiene candidatas en 14 días
- **THEN** se envía el encabezado más el aviso corto (confirma que el bot revisó)

#### Scenario: Vigía sin novedades
- **WHEN** una corrida 8:00/20:00 no encuentra nuevas urgentes
- **THEN** no se envía ningún mensaje
