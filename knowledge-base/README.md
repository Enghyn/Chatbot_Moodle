# bot-moodle — Base de Conocimiento

Base de conocimiento generada por ingest desde `docs/` (`filtros.md`, `whatsapp.md`) + specs en `openspec/specs/` + código en `src/bot_moodle/`. Modo A (silencioso).

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance v0.1, fuera de alcance, métricas |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack Python, arquitectura scraper+Evolution, integraciones, endpoints |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Operador, compañeros, profesores, admins; RBAC mínima |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Entrega, RegistroEstado, Corrida, Mensaje; `estado.json`, seed data |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-EXT/TMP/COM/URG/ENV/FMT/GLB con trazabilidad a specs |
| [06_funcionalidades.md](06_funcionalidades.md) | 3 épicas, 6 historias US-001 a US-006 con criterios |
| [07_flujos_principales.md](07_flujos_principales.md) | Digest, vigía urgente, sesión caída, go-live |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, árbol del proyecto, seguridad, env vars |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-01 a DD-07 + SU-01 a SU-04 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | IN-01/IN-02 + 6 preguntas priorizadas |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

Bot personal que avisa por WhatsApp los vencimientos de Moodle de la comisión 4 (3 cursos, 2 campus): digest semanal + vigía urgente 2x/día, filtrado por fecha y comisión, envío vía Evolution API desde VPS. Pendiente solo el trabajo vivo en VPS (login real, QR, grupo de prueba, go-live).
