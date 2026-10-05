# Proposal

## Why

El mensaje muestra encabezados genéricos repetidos (`Práctica 💻` varias veces) que no dicen a qué unidad pertenece cada entrega. Los estudiantes deben adivinarlo por la fecha o abrir Moodle. Las tabs de navegación ya traen el nombre corto de cada unidad (`CSS`, `Unidad 4`, `Módulo 2`), así que el bot puede mostrar `CSS - Práctica` sin inventar nada.

## What Changes

- Cada actividad candidata resuelve su **unidad padre**: la tab anterior más cercana en la navegación ordenada cuyo título NO sea un apartado genérico (`Práctica`, `Actividades`, `Inicio`, `Autoevaluación`, `Encuesta...`).
- El encabezado del mensaje pasa a una sola línea `{Unidad} - {Apartado}` (ej. `CSS - Práctica`, `Unidad 4 - Práctica`); reemplaza los dos encabezados actuales (sección + apartado).
- Aplica a los 3 cursos (incluido Inglés: `Módulo 2 - Class 5` si la jerarquía lo confirma en fixtures).
- Fallbacks: sin padre (apartado huérfano o primera tab) → solo el apartado, como hoy; padre igual al apartado → una sola línea (dedup vigente).

## Capabilities

### New Capabilities
- (ninguna)

### Modified Capabilities
- `message-format`: la agrupación y el encabezado cambian de Curso > Sección > Apartado (dos líneas) a Curso > `Unidad - Apartado` (una línea) con unidad derivada de las tabs.
- `moodle-extraction`: la extracción suma la unidad padre por actividad (tabs ordenadas + lista de apartados genéricos) y la agrupación usa la nueva clave.

## Impact

- Código: `sections.py` (extraer tabs ordenadas con título corto), `scrape.py`/`breadcrumbs.py` (propagar `unidad_padre` por actividad), `grouping.py` + `formatting.py` (nueva clave y plantilla de una línea), tests con fixtures (tabs reales de Prog3 y BD2).
- Sin cambios en filtros, watcher, envío ni scheduling.
- Riesgo: si un curso reordena tabs o mete un apartado con nombre no genérico, el padre puede fallar → cubierto por el fallback (apartado solo) y tests por curso.
