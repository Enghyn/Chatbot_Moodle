# Design

## Context

Ver proposal.md. Evidencia HTML verificada en fixtures: la navegación por tabs (`a.nav-link[title]`) trae títulos cortos de unidad (`CSS`, `Unidad 4`, `FastAPI`) seguidos de tabs de apartado (`Introducción`, `Actividades`, `Práctica`, `Autoevaluación`); el índice `courseindex` es plano (sin anidado) y la vista `Tema_` solo muestra la sección actual.

## Goals / Non-Goals

**Goals:**
- Resolver `unidad_padre` por actividad desde las tabs ordenadas, en los 3 cursos.
- Encabezado de una línea `{Unidad} - {Apartado}` con fallbacks que nunca rompen el mensaje.
- Tests contra fixtures reales (tabs de Prog3 y BD2) + Inglés.

**Non-Goals:**
- Cambiar filtros, watcher, envío, scheduling o fecha corta.
- Normalizar/embellecer nombres de unidad más allá del título corto de la tab.

## Decisions

### 1. Padre = tab anterior no-genérica (posicional, no DOM)
Por qué: el índice es plano y la vista Tema es parcial; lo único con jerarquía implícita y títulos cortos es el orden de tabs. Lista genérica (case-insensitive, sin emojis): `práctica/practica`, `actividades`, `inicio`, `autoevaluación/autoevaluacion`, `encuesta...`. Alternativa (parsear título largo del índice con paréntesis): descartada — frágil y verbosa para WhatsApp.

### 2. Una línea `{Unidad} - {Apartado}`, sin dos niveles
Por qué: decisión del operador con ejemplo (`CSS - Práctica`); elimina la duplicación actual y acorta el mensaje. Si padre == apartado o no hay padre, una sola línea con lo disponible (dedup vigente).

### 3. Propagación como campo nuevo, no reemplazo
`unidad_padre` viaja en el dict de candidata junto a `section`/`apartado` (se conservan para filtros y debug); `grouping.py` agrupa por la nueva clave. Migración nula: campo opcional con fallback a comportamiento anterior.

## Risks / Trade-offs

- [Apartado con nombre no genérico (ej. `Encuesta de cierre 🎓` con variante)] → Mitigación: matching por prefijo case-insensitive + fallback a apartado solo; test por curso.
- [Reorden de tabs por el docente] → Mitigación: el padre se recalcula en cada corrida desde el HTML vivo, nunca se hardcodea.
- [Inglés Module > Class sin tab padre clara] → Mitigación: validar contra fixture `tema_ingles_class5.html` en TDD; si no hay padre, formato anterior.
