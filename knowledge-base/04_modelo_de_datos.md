# Modelo de Datos

Sin base de datos: el estado vive en `estado.json`. Entidades lógicas del dominio:

## Dominios

- **Extracción**: lo que se lee de Moodle (cursos, secciones, actividades, fechas).
- **Seguimiento**: lo ya visto/notificado entre corridas (`estado.json`).
- **Notificación**: el mensaje construido (digest, actualización, aviso vacío).

## ERD (textual)

```
Entrega (1) ——< Avistaje (N, uno por corrida que la ve)
Entrega (1) ——< Notificación (0..N: digest y/o una urgente)
Corrida (1) ——< Entrega vista (N)
```

## Entidades

### Entrega
- Atributos: `assign_id` (int, clave; ej. 56812), `titulo` (verbatim), `curso` (Inglés/BD2/Prog3), `seccion` (verbatim índice), `apartado` (verbatim breadcrumb), `apertura` (datetime|None), `cierre` (datetime|None), `marcas_comision` (lista derivada del título), `url_detalle` (no se envía en V1).
- Relaciones: tiene 0..1 cierre parseable; pertenece a 1 sección y 1 apartado.
- Constraints: sin `cierre` parseable no es notificable; `assign_id` único.
- Índices: por `assign_id` (lookup del vigía).

### RegistroEstado (por assign_id, en estado.json)
- Atributos: `visto` (timestamp primer avistaje), `notificado_urgente` (bool), `notificado_digest` (bool).
- Relaciones: 1 a 1 con Entrega.
- Constraints: una urgente se alerta una sola vez (`notificado_urgente` single-shot).

### Corrida
- Atributos: `fecha_hora`, `tipo` (digest lunes 8:00 | vigía 8:00/20:00), `campus_ok` (lista), `campus_fallido` (lista).
- Relaciones: ve N entregas; produce 0..1 mensaje.

### Mensaje
- Atributos: `tipo` (digest | actualizacion | aviso_vacio), `nuevas` (ids con 🆕), `texto` (plantilla 08).
- Constraints: vigía sin novedades = cero mensajes; digest siempre produce exactamente uno.

## Seed data inicial

- `estado.json` vacío (`{}`); se puebla solo con avistajes.
- Exclusion list inicial: `UML id=1457` (Comisión 1) — ver `09_decisiones_y_supuestos.md` DD-04.
- `.env` desde `.env.example` (sin secretos reales en repo).
