# Spec Delta

## MODIFIED Requirements

### Requirement: Agrupación y omisión de vacíos
El sistema SHALL derivar por actividad su unidad padre (la tab anterior más cercana en la navegación ordenada cuyo título NO sea un apartado genérico: `Práctica`, `Actividades`, `Inicio`, `Autoevaluación`, `Encuesta...`) y SHALL agrupar candidatas por Curso > `Unidad - Apartado`, omitiendo grupos sin entregas.

#### Scenario: Apartado vacío
- **WHEN** un apartado no tiene candidatas en ventana
- **THEN** no se muestra su encabezado

#### Scenario: Nombres verbatim
- **WHEN** la sección es `UNIDAD 1: FASTAPI` duplicada o `Actividades 🚀` vs `Práctica 💻`
- **THEN** se muestra tal cual, sin normalizar ni reordenar por número

#### Scenario: Unidad derivada de tabs
- **WHEN** una entrega vive en la sección `Práctica` precedida por la tab de unidad `CSS`
- **THEN** su clave de agrupación es `CSS - Práctica` usando el título corto de la tab

#### Scenario: Semana sin vencimientos
- **WHEN** ningún curso tiene candidatas en ventana
- **THEN** el sistema produce un resultado vacío tipificado (silencio o aviso "sin vencimientos", a decidir en capa de envío)
