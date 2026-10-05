# Spec Delta

## MODIFIED Requirements

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
