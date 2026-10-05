# Tasks

## 1. Resolución de unidad padre (TDD con fixtures)

- [x] 1.1 Implementar extracción ordenada de tabs (`a.nav-link[title]` + `section=` de la URL) en `sections.py` con tests que verifican la secuencia real de Prog3 (`CSS` antes de su `Práctica`) y BD2 (`Unidad 4` antes de la suya)
- [x] 1.2 Implementar `unidad_padre` por sección (anterior no-genérica; fallback None si huérfana) y propagarla en el dict de candidata, con tests que verifican `Práctica(sec 26)` → `CSS`, `Práctica(sec 18 BD2)` → `Unidad 4`, y sección sin padre → None
- [x] 1.3 Verificar jerarquía de Inglés contra `tema_ingles_class5.html` (Module > Class) con test que fija el padre de `Class 5` o documenta el fallback si no hay tab padre

## 2. Agrupación y plantilla de una línea

- [x] 2.1 Cambiar `grouping.py` a clave `Unidad - Apartado` (fallback a comportamiento anterior sin padre) con tests que verifican que dos `Práctica` de distintas unidades ya no comparten encabezado
- [x] 2.2 Actualizar `formatting.py` al encabezado de una línea y goldens byte-a-byte del ejemplo real (`CSS - Práctica` con sus entregas) más caso fallback (apartado solo)
- [x] 2.3 Suite completa en verde y doc corta del cambio en `docs/` si la plantilla lo amerita
